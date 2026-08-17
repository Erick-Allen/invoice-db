import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import suppliers as supplier_services
from . import render_products, render_suppliers, ui


suppliers_app = typer.Typer(help="Supplier commands.")


def _handle_service_error(error: Exception) -> None:
    style = "warning" if isinstance(
        error,
        service_exceptions.NotFoundError
        | service_exceptions.ValidationError
        | service_exceptions.ConflictError,
    ) else "error"
    ui.console.print(str(error), style=style)
    raise typer.Exit(code=1)


@suppliers_app.command("add", help="Add a product supplier.")
def add_supplier(
    name: str = typer.Option(..., "-n", "--name", help="Name of the supplier."),
    phone: Optional[str] = typer.Option(None, "--phone", help="Supplier phone."),
    email: Optional[str] = typer.Option(None, "--email", help="Supplier email."),
    website: Optional[str] = typer.Option(None, "--website", help="Supplier website."),
    active: bool = typer.Option(True, "--active/--inactive", help="Initial supplier active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            supplier = supplier_services.create_supplier(
                cursor,
                name=name,
                phone=phone,
                email=email,
                website=website,
                is_active=active,
            )
        except (service_exceptions.ValidationError, service_exceptions.ServiceError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created supplier: {supplier['name']} (id={supplier['id']})", style="success")


@suppliers_app.command("list", help="List product suppliers.")
def list_suppliers(
    active_only: bool = typer.Option(False, "--active-only", help="Only list active suppliers."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            suppliers = supplier_services.list_suppliers(cursor, active_only=active_only)
        except sqlite3.Error as e:
            ui.db_error(e)

    if suppliers:
        render_suppliers.print_suppliers_table(suppliers)
    else:
        render_suppliers.no_suppliers_found()


@suppliers_app.command("get", help="Get a supplier by ID.")
def get_supplier(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            supplier = supplier_services.get_supplier_by_id(cursor, supplier_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_suppliers.print_supplier_table(supplier)


@suppliers_app.command("update", help="Update a supplier.")
def update_supplier(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier to update."),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="New supplier name."),
    phone: Optional[str] = typer.Option(None, "--phone", help="New supplier phone."),
    email: Optional[str] = typer.Option(None, "--email", help="New supplier email."),
    website: Optional[str] = typer.Option(None, "--website", help="New supplier website."),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Supplier active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    if name is None and phone is None and email is None and website is None and active is None:
        ui.console.print("Please provide at least one value to update the supplier.", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            supplier = supplier_services.update_supplier_by_id(
                cursor,
                supplier_id=supplier_id,
                name=name,
                phone=phone,
                email=email,
                website=website,
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

    ui.console.print(f"Updated supplier (id={supplier['id']})", style="success")
    render_suppliers.print_supplier_table(supplier)


@suppliers_app.command("deactivate", help="Deactivate a supplier.")
def deactivate_supplier(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier to deactivate."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            supplier = supplier_services.deactivate_supplier(cursor, supplier_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deactivated supplier (id={supplier['id']})", style="success")


@suppliers_app.command("delete", help="Delete an unused supplier.")
def delete_supplier(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier to delete."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            supplier_services.delete_supplier(cursor, supplier_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted supplier (id={supplier_id})", style="success")


@suppliers_app.command("products", help="List products attached to a supplier.")
def list_supplier_products(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            products = supplier_services.list_supplier_products(cursor, supplier_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    if products:
        render_products.print_products_table(products)
    else:
        render_products.no_products_found()


@suppliers_app.command("remove-from-products", help="Remove an inactive supplier from all products.")
def remove_supplier_from_all_products(
    supplier_id: int = typer.Option(..., "-i", "--id", help="ID of supplier."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            result = supplier_services.remove_supplier_from_all_products(cursor, supplier_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_suppliers.print_supplier_cleanup(result)
