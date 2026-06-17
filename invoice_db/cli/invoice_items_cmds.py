import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import invoice_items as invoice_item_services
from invoice_db.utils import to_cents
from . import render_invoice_items, ui


invoice_items_app = typer.Typer(help="Invoice line item commands.")


def _handle_service_error(error: Exception) -> None:
    style = "warning" if isinstance(
        error,
        (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
        ),
    ) else "error"
    ui.console.print(str(error), style=style)
    raise typer.Exit(code=1)


@invoice_items_app.command("add", help="Add a line item to a draft invoice.")
def add_invoice_item(
    invoice_id: int = typer.Option(..., "--invoice-id", help="Invoice to add this line item to."),
    product_id: int = typer.Option(..., "--product-id", help="Product to add to the invoice."),
    quantity: int = typer.Option(1, "-q", "--quantity", help="Line item quantity."),
    unit_price: Optional[float] = typer.Option(None, "--unit-price", help="Override unit price in dollars."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            item = invoice_item_services.create_invoice_item(
                cursor,
                invoice_id=invoice_id,
                product_id=product_id,
                quantity=quantity,
                unit_price_cents=to_cents(unit_price) if unit_price is not None else None,
            )
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created invoice item (id={item['id']})", style="success")
    render_invoice_items.print_invoice_item_table(item)


@invoice_items_app.command("list", help="List line items for an invoice.")
def list_invoice_items(
    invoice_id: int = typer.Option(..., "--invoice-id", help="Invoice to list line items for."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            items = invoice_item_services.list_invoice_items(cursor, invoice_id=invoice_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    if items:
        render_invoice_items.print_invoice_items_table(items)
    else:
        render_invoice_items.no_invoice_items_found()


@invoice_items_app.command("get", help="Get an invoice line item by ID.")
def get_invoice_item(
    invoice_item_id: int = typer.Option(..., "-i", "--id", help="Invoice item ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            item = invoice_item_services.get_invoice_item_by_id(cursor, invoice_item_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_invoice_items.print_invoice_item_table(item)


@invoice_items_app.command("update", help="Update a draft invoice line item.")
def update_invoice_item(
    invoice_item_id: int = typer.Option(..., "-i", "--id", help="Invoice item ID."),
    quantity: Optional[int] = typer.Option(None, "-q", "--quantity", help="New line item quantity."),
    unit_price: Optional[float] = typer.Option(None, "--unit-price", help="New unit price in dollars."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    if quantity is None and unit_price is None:
        ui.console.print("Please provide at least one value to update the invoice item.", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            item = invoice_item_services.update_invoice_item_by_id(
                cursor,
                invoice_item_id,
                quantity=quantity,
                unit_price_cents=to_cents(unit_price) if unit_price is not None else None,
            )
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Updated invoice item (id={item['id']})", style="success")
    render_invoice_items.print_invoice_item_table(item)


@invoice_items_app.command("delete", help="Delete a draft invoice line item.")
def delete_invoice_item(
    invoice_item_id: int = typer.Option(..., "-i", "--id", help="Invoice item ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoice_item_services.delete_invoice_item(cursor, invoice_item_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted invoice item (id={invoice_item_id})", style="success")
