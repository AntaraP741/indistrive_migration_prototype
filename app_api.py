import json
import os
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import hashlib

import psycopg2
from psycopg2 import sql

from assessment.dependency_engine import DependencyEngine
from assessment.risk_engine import RiskEngine
from assessment.schema_crawler import SchemaCrawler
from assessment.sizing_analyzer import SizingAnalyzer
from migration.mongo_writer import MongoWriter
from migration.migration_orchestrator import MigrationOrchestrator
from migration.postgres_reader import PostgresReader
from validation.post_migration_report import generate_post_migration_report


OUTPUT_DIR = Path("outputs")
READINESS_PATH = OUTPUT_DIR / "readiness_report.json"
POST_MIGRATION_PATH = OUTPUT_DIR / "postMigrationReport.json"


def json_response(handler, status, payload):
    body = json.dumps(payload, default=_json_default).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def parse_json_body(handler):
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(content_length) if content_length else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


def require_fields(payload, required_fields):
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Missing required request field(s): {', '.join(missing)}")


def build_pg_config(source):
    return {
        "host": source["host"],
        "port": int(source.get("port", 5432)),
        "database": source["database"],
        "user": source["user"],
        "password": source["password"],
    }


def list_accessible_schemas(cursor):
    cursor.execute(
        """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('information_schema')
          AND schema_name NOT LIKE 'pg_%'
        ORDER BY schema_name
        """
    )
    return [row[0] for row in cursor.fetchall()]


def resolve_schema_name(source, cursor):
    requested_schema = source.get("schema", "").strip()
    if requested_schema:
        return requested_schema

    cursor.execute("SELECT current_schema()")
    return cursor.fetchone()[0] or "public"


def build_mongo_target(target):
    db_name = target["database"]
    if target.get("uri"):
        return target["uri"], db_name

    host = target.get("host", "localhost")
    port = int(target.get("port", 27017))
    username = target.get("user", "").strip()
    password = target.get("password", "").strip()

    if username and password:
        uri = f"mongodb://{username}:{password}@{host}:{port}/"
    else:
        uri = f"mongodb://{host}:{port}/"

    return uri, db_name


def extract_reference_table(definition):
    marker = "REFERENCES"
    if marker not in definition:
        return None

    referenced = definition.split(marker, 1)[1].split("(")[0].strip()
    normalized = referenced.strip('"')
    if "." in normalized:
        normalized = normalized.split(".")[-1]
    return normalized.strip('"')


def row_string(values):
    return "|".join("" if value is None else str(value) for value in values)


def get_table_columns(cursor, schema_name, table_name):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
          AND table_schema = %s
        ORDER BY ordinal_position
        """,
        (table_name, schema_name),
    )
    return [row[0] for row in cursor.fetchall()]


def compute_table_checksum(conn, cursor, schema_name, table_name, columns):
    order_identifiers = [sql.Identifier(column) for column in sorted(columns)]
    query = sql.SQL("SELECT {} FROM {}.{} ORDER BY {}").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.Identifier(schema_name),
        sql.Identifier(table_name),
        sql.SQL(", ").join(order_identifiers),
    )
    cursor.execute(query)
    rows = cursor.fetchall()

    row_hashes = []
    for row in rows:
        row_hashes.append(hashlib.md5(row_string(row).encode("utf-8")).hexdigest())

    combined = "".join(sorted(row_hashes))
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def filter_snapshot(snapshot, selected_tables):
    selected_set = set(selected_tables)
    filtered = {"tables": {}}

    for table_name, meta in snapshot["tables"].items():
        if table_name not in selected_set:
            continue

        kept_constraints = []
        for constraint in meta.get("constraints", []):
            if constraint.get("type") != "f":
                kept_constraints.append(constraint)
                continue

            referenced = extract_reference_table(constraint.get("definition", ""))
            if referenced in selected_set:
                kept_constraints.append(constraint)

        filtered["tables"][table_name] = {"constraints": kept_constraints}

    return filtered


def get_table_row_count(cursor, schema, table_name):
    query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
        sql.Identifier(schema),
        sql.Identifier(table_name)
    )
    cursor.execute(query)
    return cursor.fetchone()[0]


def get_table_preview(cursor, schema, table_name, limit=5):
    query = sql.SQL("SELECT * FROM {}.{} LIMIT {}").format(
        sql.Identifier(schema),
        sql.Identifier(table_name),
        sql.Literal(limit)
    )
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def discover_schema(source):
    pg_config = build_pg_config(source)

    with psycopg2.connect(**pg_config) as conn:
        with conn.cursor() as schema_cursor:
            schema_name = resolve_schema_name(source, schema_cursor)
            available_schemas = list_accessible_schemas(schema_cursor)

        crawler = SchemaCrawler(conn, schema=schema_name)
        snapshot = crawler.crawl()
        cursor = conn.cursor()
        tables = []

        for table_name, meta in snapshot["tables"].items():
            columns = get_table_columns(cursor, schema_name, table_name)
            row_count = get_table_row_count(cursor, schema_name, table_name)
            dependencies = []

            for constraint in meta.get("constraints", []):
                if constraint.get("type") == "f":
                    referenced = extract_reference_table(constraint.get("definition", ""))
                    if referenced:
                        dependencies.append(referenced)

            tables.append(
                {
                    "name": table_name,
                    "columns": columns,
                    "rowCount": row_count,
                    "dependencies": dependencies,
                    "preview": get_table_preview(cursor, schema_name, table_name),
                }
            )

        cursor.close()
        if not tables:
            available_label = ", ".join(available_schemas) if available_schemas else "none"
            raise ValueError(
                f"No tables were found in schema '{schema_name}'. "
                f"Available schemas: {available_label}."
            )

        return {"schema": schema_name, "tables": tables, "availableSchemas": available_schemas}


def build_readiness_report(source, selected_tables):
    pg_config = build_pg_config(source)

    with psycopg2.connect(**pg_config) as conn:
        with conn.cursor() as schema_cursor:
            schema_name = resolve_schema_name(source, schema_cursor)
        crawler = SchemaCrawler(conn, schema=schema_name)
        snapshot = filter_snapshot(crawler.crawl(), selected_tables)

        dep_engine = DependencyEngine(snapshot)
        dep_engine.build_graph()
        migration_order = dep_engine.topological_sort() or list(snapshot["tables"].keys())
        dep_metrics = dep_engine.compute_metrics()

        sizing = SizingAnalyzer(conn)
        size_metrics = sizing.analyze()

        cursor = conn.cursor()
        tables_metadata = {}

        for table_name in snapshot["tables"].keys():
            columns = get_table_columns(cursor, schema_name, table_name)
            row_count = get_table_row_count(cursor, schema_name, table_name)
            checksum = compute_table_checksum(conn, cursor, schema_name, table_name, columns)
            tables_metadata[table_name] = {
                "row_count": row_count,
                "columns": columns,
                "checksum": checksum,
            }

        cursor.close()

        risk_engine = RiskEngine()
        risk_result = risk_engine.compute(dep_metrics, size_metrics, tables_metadata)

        readiness_report = {
            "tables": tables_metadata,
            "dependency_metrics": dep_metrics,
            "migration_order": migration_order,
            "size_metrics": size_metrics,
            "risk_assessment": risk_result,
        }

        OUTPUT_DIR.mkdir(exist_ok=True)
        with READINESS_PATH.open("w", encoding="utf-8") as handle:
            json.dump(readiness_report, handle, indent=2)

        return readiness_report, snapshot


def run_migration_pipeline(source, target, selected_tables):
    readiness_report, snapshot = build_readiness_report(source, selected_tables)
    pg_config = build_pg_config(source)
    mongo_uri, db_name = build_mongo_target(target)
    logs = []

    with psycopg2.connect(**pg_config) as conn:
        with conn.cursor() as schema_cursor:
            schema_name = resolve_schema_name(source, schema_cursor)

    pg_reader = PostgresReader(pg_config)
    mongo_writer = MongoWriter(uri=mongo_uri, db_name=db_name)

    try:
        orchestrator = MigrationOrchestrator(
            snapshot,
            pg_reader,
            mongo_writer,
            schema=schema_name,
            log_callback=logs.append,
        )
        orchestrator.migrate()
    finally:
        pg_reader.close()
        mongo_writer.client.close()

    validation_report = generate_post_migration_report(
        readiness_report,
        mongo_uri=mongo_uri,
        db_name=db_name,
        output_path=str(POST_MIGRATION_PATH),
    )

    return {
        "readiness": readiness_report,
        "validation": validation_report,
        "selectedTables": selected_tables,
        "logs": logs,
    }


def test_connectors(payload):
    results = {"source": None, "target": None}

    if payload.get("source"):
        pg_config = build_pg_config(payload["source"])
        with psycopg2.connect(**pg_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_schema()")
                database, current_schema = cursor.fetchone()
                schema_name = resolve_schema_name(payload["source"], cursor)
                available_schemas = list_accessible_schemas(cursor)
        results["source"] = {
            "ok": True,
            "database": database,
            "schema": schema_name,
            "currentSchema": current_schema,
            "availableSchemas": available_schemas,
        }

    if payload.get("target"):
        mongo_uri, db_name = build_mongo_target(payload["target"])
        writer = MongoWriter(uri=mongo_uri, db_name=db_name)
        writer.client.admin.command("ping")
        writer.client.close()
        results["target"] = {"ok": True, "database": db_name}

    return results


class MigrationRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        json_response(self, 204, {})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return json_response(self, 200, {"status": "ok"})

        return json_response(self, 404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        try:
            payload = parse_json_body(self)

            if parsed.path == "/api/connectors/test":
                return json_response(self, 200, test_connectors(payload))

            if parsed.path == "/api/schema/discover":
                require_fields(payload, ["source"])
                source = payload["source"]
                return json_response(self, 200, discover_schema(source))

            if parsed.path == "/api/assessment/run":
                require_fields(payload, ["source", "selectedTables"])
                readiness_report, _ = build_readiness_report(
                    payload["source"],
                    payload["selectedTables"],
                )
                return json_response(self, 200, readiness_report)

            if parsed.path == "/api/migration/run":
                require_fields(payload, ["source", "target", "selectedTables"])
                result = run_migration_pipeline(
                    payload["source"],
                    payload["target"],
                    payload["selectedTables"],
                )
                return json_response(self, 200, result)

            return json_response(self, 404, {"error": "Not found"})
        except ValueError as exc:
            return json_response(self, 400, {"error": str(exc)})
        except Exception as exc:
            return json_response(self, 500, {"error": str(exc)})


def run_server(host=None, port=None):
    host = host or os.getenv("HOST", "127.0.0.1")
    port = int(port or os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), MigrationRequestHandler)
    print(f"Migration API server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
