import psycopg2

from assessment.assessment_main import run_assessment
from config import load_mongo_config, load_pg_config, load_pg_schema
from assessment.schema_crawler import SchemaCrawler
from migration.postgres_reader import PostgresReader
from migration.mongo_writer import MongoWriter
from migration.migration_orchestrator import MigrationOrchestrator
from validation.post_migration_report import generate_post_migration_report

def run_migration():
    pg_config = load_pg_config()
    schema_name = load_pg_schema()
    mongo_config = load_mongo_config()

    # Connect once
    conn = psycopg2.connect(**pg_config)

    # Create the metadata readiness report
    run_assessment()

    # Generate fresh schema snapshot dynamically
    crawler = SchemaCrawler(conn, schema=schema_name)
    snapshot = crawler.crawl()

    # Setup data migration tools
    pg_reader = PostgresReader(pg_config)
    mongo_writer = MongoWriter(
        uri=mongo_config["uri"],
        db_name=mongo_config["database"]
    )

    # Run migration
    orchestrator = MigrationOrchestrator(
        snapshot,
        pg_reader,
        mongo_writer,
        schema=schema_name
    )

    orchestrator.migrate()

    pg_reader.close()
    conn.close()
# Generate post-migration report
    generate_post_migration_report(
        readiness_report_path="outputs/readiness_report.json",
        mongo_uri=mongo_config["uri"],
        db_name=mongo_config["database"]
    )


if __name__ == "__main__":
    run_migration()
