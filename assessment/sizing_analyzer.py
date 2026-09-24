class SizingAnalyzer:
    def __init__(self, conn):
        self.conn = conn

# Helper method to execute a query and fetch results
    def fetchall(self, query):
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

# Analyze database size, row counts, and table sizes to compute metrics
    def analyze(self):
        db_size = self.fetchall(
            "SELECT pg_database_size(current_database());"
        )[0][0]

        rows = self.fetchall("""
            SELECT relname, n_live_tup
            FROM pg_stat_user_tables;
        """)
        row_counts = {r[0]: int(r[1]) for r in rows}

        sizes = self.fetchall("""
            SELECT relname, pg_total_relation_size(relid)
            FROM pg_catalog.pg_statio_user_tables;
        """)
        table_sizes = {r[0]: int(r[1]) for r in sizes}

        total_rows = sum(row_counts.values())
        largest_table = max(table_sizes, key=table_sizes.get, default=None)

        return {
            "database_size_bytes": db_size,
            "total_rows": total_rows,
            "largest_table": largest_table,
            "largest_table_size_bytes": table_sizes.get(largest_table, 0)
        }