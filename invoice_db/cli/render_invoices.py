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

def print_invoice_table(invoice: dict) -> None:
    table = Table(title=f"Invoice (id={invoice['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")
    table.add_column("Status", justify="left")

    due = utils.fmt_optional(invoice["date_due"])
    issued = utils.fmt_optional(invoice["date_issued"])
    if due == "-":
            due = "[muted]-[/muted]"
    if issued == "-":
            issued = "[muted]-[/muted]"
    table.add_row(str(invoice['id']), str(utils.fmt_dollars(invoice['total'])), issued, due, invoice['status'])
    common.console.print(table)

def print_invoices_table(invoices: list) -> None:
    table = Table(title=f"[title]Invoices[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")
    table.add_column("Status", justify="left")

    for i in invoices:
        due = utils.fmt_optional(i["date_due"])
        issued = utils.fmt_optional(i["date_issued"])
        if due == "-":
            due = "[muted]-[/muted]"
        if issued == "-":
            issued = "[muted]-[/muted]"
        table.add_row(str(i['id']), str(utils.fmt_dollars(i['total'])), issued, due, i['status'])
    common.console.print(table)

def print_invoices_table_overdue(invoices: list) -> None:
    table = Table(title=f"[title]Overdue Invoices[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")
    table.add_column("Status", justify="left")
    table.add_column("Days_Overdue", justify="center")

    for i in invoices:
        due = utils.fmt_optional(i["date_due"])
        if due == "-":
            due = "[muted]-[/muted]"
        table.add_row(str(i['id']), str(utils.fmt_dollars(i['total'])), str(i['date_issued']), due, i['status'], str(i["days_overdue"]))
    common.console.print(table)

def build_count_label(
        customer: dict | None = None,
        status: str | None = None,
        min_total: int | None = None,
        max_total: int | None = None,
) -> str | None:
    parts = []

    if customer:
        parts.append(f"for {customer['name']}")
    if status:
        parts.append(f"status='{status}'")
    if min_total:
        parts.append(f"total >= {min_total}")
    if max_total:
        parts.append(f"total <= {max_total}")

    return ", ".join(parts) if parts else None

def build_changed_fields_label(
        customer_id: int | None = None,
        date_issued: str | None = None,
        date_due: str | None = None,
        total: int | None = None,
) -> str | None:
    changed_fields = []

    if customer_id:
        changed_fields.append("customer_id")
    if date_issued:
        changed_fields.append("date_issued")
    if date_due:
        changed_fields.append("date_due")
    if total:
        changed_fields.append("total")

    return " ".join(changed_fields) if changed_fields else None

def print_invoice_count(count: int, label: str) -> None:
    if label:
        common.console.print(f"[accent]Matched invoices: [highlight]{count}[/highlight]")
    else:
        common.console.print(f"[accent]Total invoices:[/accent] [highlight]{count}[/highlight]")

def print_invoice_update(id: int, fields: str) -> None:
    if fields:
        common.console.print(f"Updated invoice (id={id}, fields: {fields})", style="success")


def display_customer_and_invoices(customer: dict, invoices: dict) -> None:
    render_customers.print_customer_summary(customer)
    if invoices:
        print_invoices_table(customer['name'], invoices)
    else:
        no_invoices_found()
        print()