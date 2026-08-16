import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import product_categories as category_services
from . import render_product_categories, ui


product_categories_app = typer.Typer(help="Product category commands.")


def _handle_service_error(error: Exception) -> None:
    style = "warning" if isinstance(
        error,
        service_exceptions.NotFoundError | service_exceptions.ValidationError,
    ) else "error"
    ui.console.print(str(error), style=style)
    raise typer.Exit(code=1)


@product_categories_app.command("add", help="Add a product category.")
def add_product_category(
    name: str = typer.Option(..., "-n", "--name", help="Name of the product category."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Product category description."),
    active: bool = typer.Option(True, "--active/--inactive", help="Initial product category active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            category = category_services.create_product_category(
                cursor,
                name=name,
                description=description,
                is_active=active,
            )
        except (service_exceptions.ValidationError, service_exceptions.ServiceError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created product category: {category['name']} (id={category['id']})", style="success")


@product_categories_app.command("list", help="List product categories.")
def list_product_categories(
    active_only: bool = typer.Option(False, "--active-only", help="Only list active product categories."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            categories = category_services.list_product_categories(cursor, active_only=active_only)
        except sqlite3.Error as e:
            ui.db_error(e)

    if categories:
        render_product_categories.print_product_categories_table(categories)
    else:
        render_product_categories.no_product_categories_found()


@product_categories_app.command("update", help="Update a product category.")
def update_product_category(
    category_id: int = typer.Option(..., "-i", "--id", help="ID of product category to update."),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="New product category name."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="New product category description."),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Product category active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    if name is None and description is None and active is None:
        ui.console.print("Please provide at least one value to update the product category.", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            category = category_services.update_product_category_by_id(
                cursor,
                category_id=category_id,
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

    ui.console.print(f"Updated product category (id={category['id']})", style="success")
    render_product_categories.print_product_category_table(category)


@product_categories_app.command("deactivate", help="Deactivate a product category.")
def deactivate_product_category(
    category_id: int = typer.Option(..., "-i", "--id", help="ID of product category to deactivate."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            category = category_services.deactivate_product_category(cursor, category_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deactivated product category (id={category['id']})", style="success")


@product_categories_app.command("delete", help="Delete an unused product category.")
def delete_product_category(
    category_id: int = typer.Option(..., "-i", "--id", help="ID of product category to delete."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            category_services.delete_product_category(cursor, category_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted product category (id={category_id})", style="success")
