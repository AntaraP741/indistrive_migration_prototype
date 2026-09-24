import json
import psycopg2
import hashlib

from config import load_pg_config, load_pg_schema
from assessment.schema_crawler import SchemaCrawler
from assessment.dependency_engine import DependencyEngine
from assessment.sizing_analyzer import SizingAnalyzer
from assessment.risk_engine import RiskEngine


def _row_string(values):
    # consistent serialization (no keys, only values)
    return "|".join(["" if v is None else str(v) for v in values])


def compute_table_checksum(cursor, table_name, columns):
 
    columns = sorted(columns)  

    order_by = ", ".join(columns)
    cursor.execute(
        f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY {order_by}"
    )

    rows = cursor.fetchall()

    row_hashes = []
    for row in rows:
        row_string = _row_string(row)
        row_hash = hashlib.md5(row_string.encode()).hexdigest()
        row_hashes.append(row_hash)

    # order-independent combine
    combined = "".join(sorted(row_hashes))
    return hashlib.md5(combined.encode()).hexdigest()


def get_table_columns(cursor, table_name):
    schema_name = load_pg_schema()

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        AND table_schema = %s
        ORDER BY ordinal_position
    """, (table_name, schema_name))

    return [row[0] for row in cursor.fetchall()]


def get_table_metadata(conn, snapshot):
    cursor = conn.cursor()
    tables_metadata = {}

    for table_name in snapshot["tables"].keys():

        columns = get_table_columns(cursor, table_name)

        # row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        # checksum
        checksum = compute_table_checksum(cursor, table_name, columns)

        tables_metadata[table_name] = {
            "row_count": row_count,
            "columns": columns,   
            "checksum": checksum
        }

    cursor.close()
    return tables_metadata


def run_assessment():
    pg_config = load_pg_config()
    schema_name = load_pg_schema()

    with psycopg2.connect(**pg_config) as conn:

        # Schema extraction
        crawler = SchemaCrawler(conn, schema=schema_name)
        snapshot = crawler.crawl()

        # Dependency analysis
        dep_engine = DependencyEngine(snapshot)
        dep_engine.build_graph()
        migration_order = dep_engine.topological_sort()
        dep_metrics = dep_engine.compute_metrics()

        # Size analysis
        sizing = SizingAnalyzer(conn)
        size_metrics = sizing.analyze()

        # Table metadata (includes checksum)
        tables_metadata = get_table_metadata(conn, snapshot)

        # Risk scoring (system-level)
        risk_engine = RiskEngine()
        risk_result = risk_engine.compute(dep_metrics, size_metrics, tables_metadata)

        readiness_report = {
            "tables": tables_metadata,
            "dependency_metrics": dep_metrics,
            "migration_order": migration_order,
            "size_metrics": size_metrics,
            "risk_assessment": risk_result
        }

        with open("outputs/readiness_report.json", "w") as f:
            json.dump(readiness_report, f, indent=2)

        print("Readiness report generated with metadata.")


if __name__ == "__main__":
    run_assessment()
