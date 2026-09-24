import psycopg2


class SchemaCrawler:
    def __init__(self, conn, schema="public"):
        self.conn = conn
        self.schema = schema

    def fetchall(self, query, params=None):
        with self.conn.cursor() as cur:
            if params is None:
                cur.execute(query)
            else:
                cur.execute(query, params)
            return cur.fetchall()

    def get_tables(self):
        rows = self.fetchall("""
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname = %s
            ORDER BY c.relname;
        """, (self.schema,))
        return [r[0] for r in rows]

    def get_constraints(self, table):
        rows = self.fetchall("""
            SELECT con.contype, pg_get_constraintdef(con.oid)
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = rel.relnamespace
            WHERE rel.relname = %s
              AND n.nspname = %s;
        """, (table, self.schema))
        return [{"type": r[0], "definition": r[1]} for r in rows]

    def crawl(self):
        snapshot = {"tables": {}}
        tables = self.get_tables()

        for table in tables:
            snapshot["tables"][table] = {
                "constraints": self.get_constraints(table)
            }

        return snapshot
