class DocumentBuilder:
    def __init__(self, embed_map):
        self.embed_map = embed_map

    def build_documents(self, parent_table, parent_rows, child_table, child_rows, fk_column):
        documents = []

        for parent in parent_rows:
            parent_id = parent["_id"]

            embedded_children = [
                child for child in child_rows
                if child[fk_column] == parent_id
            ]

            doc = parent.copy()
            doc[child_table] = embedded_children

            documents.append(doc)

        return documents