import re
from collections import defaultdict, deque


class DependencyEngine:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.graph = defaultdict(set)

# Build a directed graph where edges represent foreign key dependencies
    def build_graph(self):
        for table, meta in self.snapshot["tables"].items():
            self.graph[table]
            for constraint in meta.get("constraints", []):
                if constraint["type"] == "f":
                    match = re.search(
                        r"REFERENCES\s+([^\s(]+)",
                        constraint["definition"],
                        re.IGNORECASE
                    )
                    if match:
                        referenced = match.group(1)
                        if "." in referenced:
                            referenced = referenced.split(".")[-1]
                        referenced = referenced.strip('"')
                        if referenced in self.snapshot["tables"]:
                            self.graph[table].add(referenced)
        return self.graph
# Perform topological sort to determine migration order
    def topological_sort(self):
        in_degree = {node: 0 for node in self.graph}
        for node in self.graph:
            for neighbor in self.graph[node]:
                in_degree[neighbor] += 1

        queue = deque([n for n in in_degree if in_degree[n] == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in self.graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.graph):
            return None
        return order
    
# Compute simple metrics like total tables and dependencies
    def compute_metrics(self):
        total_edges = sum(len(v) for v in self.graph.values())
        return {
            "total_tables": len(self.graph),
            "total_dependencies": total_edges
        }
