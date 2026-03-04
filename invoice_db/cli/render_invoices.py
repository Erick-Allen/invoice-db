from invoice_db.db import utils
from . import common, render_customers
from rich.table import Table

def invoice_not_found(invoice_id: int | None = None) -> None:
    if invoice_id is not None:
        common.console.print(f"Invoice not found (id={invoice_id})", style ="warning")
    else:
        common.console.print("Invoice not found", style="warning")

def no_invoices_found() -> None:
    common.console.print("No invoices found", style="warning")

def print_invoice_table(invoice) -> None:
    table = Table(title=f"Invoice (id={invoice['invoice_id']})")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")

    due = utils.fmt_optional(invoice["date_due"])
    if due == "-":
            due = "[muted]-[/muted]"
    table.add_row(str(invoice['invoice_id']), str(utils.fmt_dollars(invoice['total'])), str(invoice['date_issued']), due)
    common.console.print(table)

def print_invoices_table(customer, invoices) -> None:
    table = Table(title=f"[title]{customer} Invoices[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center", style="muted")
    table.add_column("Due", justify="center")

    for i in invoices:
        due = utils.fmt_optional(i["date_due"])
        if due == "-":
            due = "[muted]-[/muted]"
        table.add_row(str(i['invoice_id']), str(utils.fmt_dollars(i['total'])), str(i['date_issued']), due)
    common.console.print(table)

def print_invoice_count(count, customer) -> None:
    if customer:
        common.console.print(f"Invoices [accent]for[/accent] {customer['name']}: [highlight]{count}[/highlight]")
    else:
        common.console.print(f"Total number of invoices: [highlight]{count}[/highlight]")

def display_customer_and_invoices(customer, invoices) -> None:
    render_customers.print_customer_summary(customer)
    if invoices:
        print_invoices_table(customer['name'], invoices)
    else:
        no_invoices_found()
        print()