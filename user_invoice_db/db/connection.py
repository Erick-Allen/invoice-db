import sqlite3
from contextlib import contextmanager
import os


DB_PATH = os.getenv("USERDB_PATH", "userdb.sqlite")

# HELPERS
def open_db(db_file=DB_PATH):
    connect = sqlite3.connect(db_file)
    connect.execute("PRAGMA foreign_keys = ON;")
    connect.execute("PRAGMA recursive_triggers = OFF;")
    connect.row_factory = sqlite3.Row
    return connect

@contextmanager
def db_session(db_file=DB_PATH):
    connect = open_db(db_file)
    try:
        yield connect, connect.cursor()
        connect.commit()
    except Exception:
        connect.rollback()
        raise
    finally:
        connect.close()



