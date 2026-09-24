import psycopg2
from psycopg2 import sql


class PostgresReader:
    def __init__(self, config):
        self.conn = psycopg2.connect(**config)
        self.conn.autocommit = False  # critical for server-side cursors

    def stream_table(self, table, schema="public", batch_size=5000):
        cursor = self.conn.cursor()

        query = sql.SQL("SELECT * FROM {}.{}").format(
            sql.Identifier(schema),
            sql.Identifier(table)
        )
        print("Running query:", query.as_string(self.conn))

        cursor.execute(query)

        print("Cursor description:", cursor.description)

        columns = [desc[0] for desc in cursor.description]

        rows = cursor.fetchall()

        for row in rows:
            yield dict(zip(columns, row))

    def close(self):
        self.conn.close()
