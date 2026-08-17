from rich.table import Table

from invoice_db import utils
from . import ui


def no_suppliers_found() -> None:
    ui.console.print("No suppliers found", style="warning")


def print_supplier_table(supplier: dict) -> None:
    table = Table(title=f"Supplier (id={supplier['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Phone")
    table.add_column("Email")
    table.add_column("Website")
    table.add_column("Active", justify="center")

    table.add_row(
        str(supplier["id"]),
        supplier["name"],
        utils.fmt_optional(supplier["phone"]),
        utils.fmt_optional(supplier["email"]),
        utils.fmt_optional(supplier["website"]),
        "yes" if supplier["is_active"] else "no",
    )
    ui.console.print(table)


def print_suppliers_table(suppliers: list[dict], title: str = "[title]Suppliers[/title]") -> None:
    table = Table(title=title)
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Phone")
    table.add_column("Email")
    table.add_column("Website")
    table.add_column("Active", justify="center")

    for supplier in suppliers:
        table.add_row(
            str(supplier["id"]),
            supplier["name"],
            utils.fmt_optional(supplier["phone"]),
            utils.fmt_optional(supplier["email"]),
            utils.fmt_optional(supplier["website"]),
            "yes" if supplier["is_active"] else "no",
        )

    ui.console.print(table)


def print_product_supplier_table(product_supplier: dict) -> None:
    table = Table(title="[title]Product Supplier[/title]")
    table.add_column("Product", justify="right")
    table.add_column("Supplier", justify="right")
    table.add_column("Note")

    table.add_row(
        str(product_supplier["product_id"]),
        str(product_supplier["supplier_id"]),
        product_supplier["note"] or "[muted]-[/muted]",
    )
    ui.console.print(table)


def print_supplier_cleanup(result: dict) -> None:
    ui.console.print(
        f"Removed supplier (id={result['supplier_id']}) from {result['removed_count']} products",
        style="success",
    )
