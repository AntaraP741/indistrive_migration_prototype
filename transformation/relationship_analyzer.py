class RelationshipAnalyzer:
    def __init__(self, canonical_model):
        self.model = canonical_model

    def analyze(self):
        relationships = []

        for entity in self.model["entities"]:
            for fk in entity["foreign_keys"]:
                relationships.append({
                    "parent": fk["references"],
                    "child": entity["name"],
                    "type": "one_to_many"
                })

        return relationships