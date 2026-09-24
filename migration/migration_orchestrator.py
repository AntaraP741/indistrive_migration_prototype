from transformation.canonical_model import CanonicalModelBuilder
from transformation.relationship_analyzer import RelationshipAnalyzer
from transformation.embeddings_engine import EmbeddingEngine
from transformation.document_builder import DocumentBuilder


class MigrationOrchestrator:
    def __init__(self, schema_snapshot, pg_reader, mongo_writer, schema="public", log_callback=None):
        self.snapshot = schema_snapshot
        self.pg_reader = pg_reader
        self.mongo_writer = mongo_writer
        self.schema = schema
        self.log_callback = log_callback

    def _log(self, message, **extra):
        print(message)
        if self.log_callback:
            self.log_callback({"message": message, **extra})

    def migrate(self):
        # Build Canonical Model
        canonical_builder = CanonicalModelBuilder(self.snapshot)
        canonical_model = canonical_builder.build()

        # Analyze Relationships
        analyzer = RelationshipAnalyzer(canonical_model)
        relationships = analyzer.analyze()

        # Decide Embedding
        embedding_engine = EmbeddingEngine(canonical_model, relationships)
        embed_map = embedding_engine.decide()

        self._log("Embedding strategy generated.", embed_map=embed_map)

        # Migrate Data
        for entity in canonical_model["entities"]:
            table = entity["name"]

            # If table is embedded into another, skip standalone migration
            if any(table in children for children in embed_map.values()):
                self._log(
                    f"Skipped standalone migration for {table} because it is embedded.",
                    table=table,
                    status="skipped"
                )
                continue

            self._log(f"Migrating {table}...", table=table, status="running")

            # Stream parent table
            parent_rows = list(self.pg_reader.stream_table(table, schema=self.schema))
            # Convert PK to _id
            pk = entity["primary_key"]
            for row in parent_rows:
                if pk and pk in row:
                    row["_id"] = row[pk]

            # Handle embedding
            if table in embed_map:
                for child_table in embed_map[table]:

                    # Get FK column from canonical model
                    child_entity = next(
                        e for e in canonical_model["entities"]
                        if e["name"] == child_table
                    )

                    fk_column = child_entity["foreign_keys"][0]["column"]

                    child_rows = list(self.pg_reader.stream_table(child_table, schema=self.schema))

                    builder = DocumentBuilder(embed_map)
                    parent_rows = builder.build_documents(
                        table,
                        parent_rows,
                        child_table,
                        child_rows,
                        fk_column
                    )

            # Write to Mongo
            self.mongo_writer.clear_collection(table)
            self.mongo_writer.insert_batch(table, parent_rows)

            self._log(
                f"{table} migrated successfully.",
                table=table,
                status="completed",
                migrated_count=len(parent_rows)
            )
