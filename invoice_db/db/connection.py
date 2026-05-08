import sqlite3
from contextlib import contextmanager
import os


DB_PATH = os.getenv("INVOICEDB_PATH", "invoicedb.sqlite")


@contextmanager
def db_session(db_path: str = DB_PATH):
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connect, cursor
        connect.commit()
    except Exception:
        connect.rollback()
        raise
    finally:
        connect.close()


