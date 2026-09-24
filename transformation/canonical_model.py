class CanonicalModelBuilder:
    def __init__(self, schema_snapshot):
        self.snapshot = schema_snapshot

    def build(self):
        entities = []

        if "tables" not in self.snapshot:
            raise Exception("Snapshot does not contain 'tables' key")

        for table_name, meta in self.snapshot["tables"].items():

            entity = {
                "name": table_name,
                "primary_key": None,
                "foreign_keys": []
            }

            for constraint in meta.get("constraints", []):
                ctype = constraint.get("type")
                definition = constraint.get("definition", "")

                # PRIMARY KEY
                if ctype == "p":
                    pk_col = definition.split("(")[1].split(")")[0]
                    entity["primary_key"] = pk_col.strip()

                # FOREIGN KEY
                elif ctype == "f":
                    local_col = definition.split("(")[1].split(")")[0]
                    ref_table = definition.split("REFERENCES")[1].split("(")[0].strip()

                    entity["foreign_keys"].append({
                        "column": local_col.strip(),
                        "references": ref_table
                    })

            entities.append(entity)

        return {"entities": entities}