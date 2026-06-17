import os
import sys

from invoice_db.db import connection, schema


def initialize_database() -> None:
    db_path = connection.DB_PATH
    db_dir = os.path.dirname(db_path)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with connection.db_session(db_path) as (_connect, cursor):
        schema.create_schema(cursor)

    print(f"Initialized database schema at {db_path}", flush=True)


if __name__ == "__main__":
    initialize_database()
    os.execvp(sys.argv[1], sys.argv[1:])
