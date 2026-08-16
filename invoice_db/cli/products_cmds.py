import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import products as products_services
from invoice_db.utils import to_cents
from . import render_products, ui


products_app = typer.Typer(help="Product commands.")


def _handle_service_error(error: Exception) -> None:
    style = "warning" if isinstance(
        error,
        service_exceptions.NotFoundError | service_exceptions.ValidationError
    ) else "error"
    ui.console.print(str(error), style=style)
    raise typer.Exit(code=1)


@products_app.command("add", help="Add a product to the catalog.")
def add_product(
    name: str = typer.Option(..., "-n", "--name", help="Name of the product."),
    unit_price: float = typer.Option(..., "-p", "--price", help="Unit price in dollars."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Product description."),
    category_id: int = typer.Option(1, "--category-id", help="Product category ID."),
    active: bool = typer.Option(True, "--active/--inactive", help="Initial product active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            product = products_services.create_product(
                cursor,
                name=name,
                description=description,
                unit_price_cents=to_cents(unit_price),
                category_id=category_id,
                is_active=active,
            )
        except (service_exceptions.ValidationError, service_exceptions.ServiceError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created product: {product['name']} (id={product['id']})", style="success")


@products_app.command("list", help="List products in the catalog.")
def list_products(
    active_only: bool = typer.Option(False, "--active-only", help="Only list active products."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            products = products_services.list_products(cursor, active_only=active_only)
        except sqlite3.Error as e:
            ui.db_error(e)

    if products:
        render_products.print_products_table(products)
    else:
        render_products.no_products_found()


@products_app.command("get", help="Get a product by ID.")
def get_product(
    product_id: int = typer.Option(..., "-i", "--id", help="ID of product to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            product = products_services.get_product_by_id(cursor, product_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_products.print_product_table(product)


@products_app.command("update", help="Update a product.")
def update_product(
    product_id: int = typer.Option(..., "-i", "--id", help="ID of product to update."),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="New product name."),
    unit_price: Optional[float] = typer.Option(None, "-p", "--price", help="New unit price in dollars."),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="New product description."),
    category_id: Optional[int] = typer.Option(None, "--category-id", help="New product category ID."),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Product active state."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    if name is None and unit_price is None and description is None and category_id is None and active is None:
        ui.console.print("Please provide at least one value to update the product.", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            product = products_services.update_product_by_id(
                cursor,
                product_id=product_id,
                name=name,
                description=description,
                unit_price_cents=to_cents(unit_price) if unit_price is not None else None,
                category_id=category_id,
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

    ui.console.print(f"Updated product (id={product['id']})", style="success")
    render_products.print_product_table(product)


@products_app.command("deactivate", help="Deactivate a product without deleting it.")
def deactivate_product(
    product_id: int = typer.Option(..., "-i", "--id", help="ID of product to deactivate."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            product = products_services.deactivate_product(cursor, product_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deactivated product (id={product['id']})", style="success")


@products_app.command("delete", help="Delete a product from the catalog.")
def delete_product(
    product_id: int = typer.Option(..., "-i", "--id", help="ID of product to delete."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            products_services.delete_product(cursor, product_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted product (id={product_id})", style="success")
