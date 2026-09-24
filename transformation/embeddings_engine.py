class EmbeddingEngine:
    def __init__(self, canonical_model, relationships):
        self.model = canonical_model
        self.relationships = relationships

    def decide(self):
        embed_map = {}

        child_reference_count = {}

        for rel in self.relationships:
            child = rel["child"]
            child_reference_count[child] = child_reference_count.get(child, 0) + 1

        for rel in self.relationships:
            parent = rel["parent"]
            child = rel["child"]

            if child_reference_count.get(child, 0) == 1:
                embed_map.setdefault(parent, []).append(child)

        return embed_map