import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import tags as tag_services
from . import render_tags, ui


tags_app = typer.Typer(help="Tag commands.")


def _handle_service_error(error: Exception) -> None:
    style = "warning" if isinstance(
        error,
        service_exceptions.NotFoundError | service_exceptions.ValidationError,
    ) else "error"
    ui.console.print(str(error), style=style)
    raise typer.Exit(code=1)


@tags_app.command("add", help="Add a reusable invoice tag.")
def add_tag(
    name: str = typer.Option(..., "-n", "--name", help="Name of the tag."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Tag description."),
    active: bool = typer.Option(True, "--active/--inactive", help="Initial tag active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            tag = tag_services.create_tag(
                cursor,
                name=name,
                description=description,
                is_active=active,
            )
        except (service_exceptions.ValidationError, service_exceptions.ServiceError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created tag: {tag['name']} (id={tag['id']})", style="success")


@tags_app.command("list", help="List reusable invoice tags.")
def list_tags(
    active_only: bool = typer.Option(False, "--active-only", help="Only list active tags."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            tags = tag_services.list_tags(cursor, active_only=active_only)
        except sqlite3.Error as e:
            ui.db_error(e)

    if tags:
        render_tags.print_tags_table(tags)
    else:
        render_tags.no_tags_found()


@tags_app.command("get", help="Get a tag by ID.")
def get_tag(
    tag_id: int = typer.Option(..., "-i", "--id", help="ID of tag to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            tag = tag_services.get_tag_by_id(cursor, tag_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_tags.print_tag_table(tag)


@tags_app.command("update", help="Update a reusable invoice tag.")
def update_tag(
    tag_id: int = typer.Option(..., "-i", "--id", help="ID of tag to update."),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="New tag name."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="New tag description."),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Tag active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    if name is None and description is None and active is None:
        ui.console.print("Please provide at least one value to update the tag.", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            tag = tag_services.update_tag_by_id(
                cursor,
                tag_id=tag_id,
                name=name,
                description=description,
                is_active=active,
            )
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Updated tag (id={tag['id']})", style="success")
    render_tags.print_tag_table(tag)


@tags_app.command("deactivate", help="Deactivate a reusable invoice tag.")
def deactivate_tag(
    tag_id: int = typer.Option(..., "-i", "--id", help="ID of tag to deactivate."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            tag = tag_services.deactivate_tag(cursor, tag_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deactivated tag (id={tag['id']})", style="success")


@tags_app.command("delete", help="Delete an unused reusable invoice tag.")
def delete_tag(
    tag_id: int = typer.Option(..., "-i", "--id", help="ID of tag to delete."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            tag_services.delete_tag(cursor, tag_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted tag (id={tag_id})", style="success")
