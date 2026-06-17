from rich.table import Table

from invoice_db import utils
from . import ui


def no_invoice_items_found() -> None:
    ui.console.print("No invoice items found", style="warning")


def print_invoice_item_table(item: dict) -> None:
    table = Table(title=f"Invoice Item (id={item['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Invoice", justify="right")
    table.add_column("Product", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Unit Price", justify="right")
    table.add_column("Line Total", justify="right")

    table.add_row(
        str(item["id"]),
        str(item["invoice_id"]),
        str(item["product_id"]),
        str(item["quantity"]),
        utils.fmt_dollars(item["unit_price_cents"]),
        utils.fmt_dollars(item["line_total_cents"]),
    )
    ui.console.print(table)


def print_invoice_items_table(items: list[dict]) -> None:
    table = Table(title="[title]Invoice Items[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Invoice", justify="right")
    table.add_column("Product", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Unit Price", justify="right")
    table.add_column("Line Total", justify="right")

    for item in items:
        table.add_row(
            str(item["id"]),
            str(item["invoice_id"]),
            str(item["product_id"]),
            str(item["quantity"]),
            utils.fmt_dollars(item["unit_price_cents"]),
            utils.fmt_dollars(item["line_total_cents"]),
        )

    ui.console.print(table)
