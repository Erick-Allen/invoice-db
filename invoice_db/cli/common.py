import typer, sqlite3
from rich.theme import Theme
from rich.console import Console
from contextlib import contextmanager
from invoice_db.db import connection

THEME = Theme({
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "danger": "bold red",
    "accent": "magenta",
    "highlight": "cyan",
    "muted": "dim",
    "title": "bold",
})

console = Console(highlight=False, theme=THEME)

@contextmanager
def get_connection(db_path=connection.DB_PATH):
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

def db_error(e: Exception) -> None:
    console.print(f"Database error: {e}", style="error")
    raise typer.Exit(code=1)
