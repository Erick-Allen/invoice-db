import sqlite3
from typing import Optional

import typer

from invoice_db.db import connection
from invoice_db.db.payments import VALID_PAYMENT_METHODS
from invoice_db.services import exceptions as service_exceptions
from invoice_db.services import payments as payment_services
from invoice_db.utils import to_cents
from . import render_payments, ui


payments_app = typer.Typer(help="Payment commands.")


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


def _method_help() -> str:
    return "Payment method: " + " | ".join(sorted(VALID_PAYMENT_METHODS))


@payments_app.command("add", help="Add a payment to a sent invoice.")
def add_payment(
    invoice_id: int = typer.Option(..., "--invoice-id", help="Invoice receiving this payment."),
    amount: float = typer.Option(..., "-a", "--amount", help="Payment amount in dollars."),
    payment_date: str = typer.Option(..., "--payment-date", help="Payment date."),
    method: str = typer.Option(..., "-m", "--method", help=_method_help()),
    note: Optional[str] = typer.Option(None, "-n", "--note", help="Optional payment note."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            payment = payment_services.create_payment(
                cursor,
                invoice_id=invoice_id,
                amount_cents=to_cents(amount),
                payment_date=payment_date,
                method=method,
                note=note,
            )
            summary = payment_services.get_payment_summary(cursor, invoice_id)
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created payment (id={payment['id']})", style="success")
    render_payments.print_payment_table(payment)
    render_payments.print_payment_summary(summary)


@payments_app.command("list", help="List payments for an invoice.")
def list_payments(
    invoice_id: int = typer.Option(..., "--invoice-id", help="Invoice to list payments for."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            payments = payment_services.list_payments(cursor, invoice_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    if payments:
        render_payments.print_payments_table(payments)
    else:
        render_payments.no_payments_found()


@payments_app.command("get", help="Get a payment by ID.")
def get_payment(
    payment_id: int = typer.Option(..., "-i", "--id", help="Payment ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            payment = payment_services.get_payment_by_id(cursor, payment_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_payments.print_payment_table(payment)


@payments_app.command("summary", help="Show payment summary for an invoice.")
def payment_summary(
    invoice_id: int = typer.Option(..., "--invoice-id", help="Invoice to summarize payments for."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            summary = payment_services.get_payment_summary(cursor, invoice_id)
        except (service_exceptions.ValidationError, service_exceptions.NotFoundError) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_payments.print_payment_summary(summary)


@payments_app.command("delete", help="Delete a payment.")
def delete_payment(
    payment_id: int = typer.Option(..., "-i", "--id", help="Payment ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            payment = payment_services.get_payment_by_id(cursor, payment_id)
            payment_services.delete_payment(cursor, payment_id)
            summary = payment_services.get_payment_summary(cursor, payment["invoice_id"])
        except (
            service_exceptions.ValidationError,
            service_exceptions.NotFoundError,
            service_exceptions.ConflictError,
            service_exceptions.ServiceError,
        ) as e:
            _handle_service_error(e)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted payment (id={payment_id})", style="success")
    render_payments.print_payment_summary(summary)
