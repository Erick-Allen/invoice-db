import sqlite3
from contextlib import contextmanager
import os


DB_PATH = os.getenv("INVOICEDB_PATH", "invoicedb.sqlite")
_INITIALIZED_DB_PATHS: set[str] = set()


def _ensure_schema(cursor, db_path: str) -> None:
    if db_path == ":memory:":
        from invoice_db.db import schema

        schema.create_schema(cursor)
        return

    resolved_path = os.path.abspath(db_path)
    if resolved_path in _INITIALIZED_DB_PATHS:
        return

    from invoice_db.db import schema

    schema.create_schema(cursor)
    cursor.connection.commit()
    _INITIALIZED_DB_PATHS.add(resolved_path)


@contextmanager
def db_session(db_path: str = DB_PATH):
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    _ensure_schema(cursor, db_path)
    try:
        yield connect, cursor
        connect.commit()
    except Exception:
        connect.rollback()
        raise
    finally:
        connect.close()
