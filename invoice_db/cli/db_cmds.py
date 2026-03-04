import typer
from rich.prompt import Confirm

from invoice_db.db import schema, connection
from .common import console, get_connection

db_app = typer.Typer(help="Database commands.")

@db_app.command("init", help="Initialize a new database with all tables and schema.")
def init_db_command(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        schema.create_customer_schema(cursor)
        schema.create_invoice_schema(cursor)
        connect.commit()
    console.print("Initialized database", style="success")


@db_app.command("drop", help="Drop all database tables (does not delete file).")
def drop_db_command(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("DROP TABLE IF EXISTS customers;")
        connect.commit()
    console.print(f"Dropped all tables from {db_path}", style="success")


@db_app.command("delete", help="Permanently delete the database file from disk.")
def delete_db_file(
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    import os  # Used only for safe local file operations (e.g., deleting DB)
    if not os.path.exists(db_path):
        console.print(f"No database found at {db_path}", style="error")
        raise typer.Exit(code=1)
    
    confirm = Confirm.ask(f"[danger]Are you sure you want to permanently delete '{db_path}'?[/danger]")
    if not confirm:
        console.print(f"Deletion cancelled", style="warning")
        raise typer.Exit(code=0)
    
    os.remove(db_path)
    console.print(f"Database file '{db_path}' deleted successfully", style="success")
