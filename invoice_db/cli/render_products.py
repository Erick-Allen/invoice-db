from rich.table import Table

from invoice_db import utils
from . import ui


def product_not_found(product_id: int | None = None) -> None:
    if product_id is not None:
        ui.console.print(f"Product not found (id={product_id})", style="warning")
    else:
        ui.console.print("Product not found", style="warning")


def no_products_found() -> None:
    ui.console.print("No products found", style="warning")


def print_product_table(product: dict) -> None:
    table = Table(title=f"Product (id={product['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Price", justify="right")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    table.add_row(
        str(product["id"]),
        product["name"],
        utils.fmt_dollars(product["unit_price_cents"]),
        "yes" if product["is_active"] else "no",
        product["description"] or "[muted]-[/muted]",
    )
    ui.console.print(table)


def print_products_table(products: list[dict]) -> None:
    table = Table(title="[title]Products[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Price", justify="right")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    for product in products:
        table.add_row(
            str(product["id"]),
            product["name"],
            utils.fmt_dollars(product["unit_price_cents"]),
            "yes" if product["is_active"] else "no",
            product["description"] or "[muted]-[/muted]",
        )

    ui.console.print(table)
