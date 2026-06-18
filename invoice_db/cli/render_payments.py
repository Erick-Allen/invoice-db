from rich.table import Table

from invoice_db import utils
from . import ui


def no_payments_found() -> None:
    ui.console.print("No payments found", style="warning")


def print_payment_table(payment: dict) -> None:
    table = Table(title=f"Payment (id={payment['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Invoice", justify="right")
    table.add_column("Amount", justify="right")
    table.add_column("Date", justify="center")
    table.add_column("Method")
    table.add_column("Note")

    table.add_row(
        str(payment["id"]),
        str(payment["invoice_id"]),
        utils.fmt_dollars(payment["amount_cents"]),
        payment["payment_date"],
        payment["method"],
        payment["note"] or "[muted]-[/muted]",
    )
    ui.console.print(table)


def print_payments_table(payments: list[dict]) -> None:
    table = Table(title="[title]Payments[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Invoice", justify="right")
    table.add_column("Amount", justify="right")
    table.add_column("Date", justify="center")
    table.add_column("Method")
    table.add_column("Note")

    for payment in payments:
        table.add_row(
            str(payment["id"]),
            str(payment["invoice_id"]),
            utils.fmt_dollars(payment["amount_cents"]),
            payment["payment_date"],
            payment["method"],
            payment["note"] or "[muted]-[/muted]",
        )

    ui.console.print(table)


def print_payment_summary(summary: dict) -> None:
    table = Table(title=f"Payment Summary for Invoice {summary['invoice_id']}")
    table.add_column("Invoice Total", justify="right")
    table.add_column("Amount Paid", justify="right")
    table.add_column("Balance Due", justify="right")
    table.add_column("Paid", justify="center")

    table.add_row(
        utils.fmt_dollars(summary["invoice_total_cents"]),
        utils.fmt_dollars(summary["amount_paid_cents"]),
        utils.fmt_dollars(summary["balance_due_cents"]),
        "yes" if summary["is_paid"] else "no",
    )
    ui.console.print(table)
