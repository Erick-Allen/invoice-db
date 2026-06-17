import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import TypedDict

from invoice_db.db import invoices as invoices_db
from invoice_db.db import payments as payments_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


class PaymentRecord(TypedDict):
    id: int
    invoice_id: int
    amount_cents: int
    payment_date: str
    method: str
    note: str | None
    created_at: str
    updated_at: str


class PaymentSummaryRecord(TypedDict):
    invoice_id: int
    invoice_total_cents: int
    amount_paid_cents: int
    balance_due_cents: int
    is_paid: bool


@contextmanager
def _payment_transaction(cursor):
    cursor.execute("SAVEPOINT payment_service")
    try:
        yield
    except Exception:
        cursor.execute("ROLLBACK TO SAVEPOINT payment_service")
        cursor.execute("RELEASE SAVEPOINT payment_service")
        raise
    else:
        cursor.execute("RELEASE SAVEPOINT payment_service")


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _validate_id(value: int, label: str) -> None:
    try:
        validate_positive_id(value, label)
    except ValueError as e:
        raise _as_validation_error(e) from e


def _to_payment_record(payment: payments_db.Payment) -> PaymentRecord:
    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "amount_cents": payment.amount_cents,
        "payment_date": payment.payment_date,
        "method": payment.method,
        "note": payment.note,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }


def _to_payment_summary_record(summary: payments_db.PaymentSummary) -> PaymentSummaryRecord:
    return {
        "invoice_id": summary.invoice_id,
        "invoice_total_cents": summary.invoice_total_cents,
        "amount_paid_cents": summary.amount_paid_cents,
        "balance_due_cents": summary.balance_due_cents,
        "is_paid": summary.is_paid,
    }


def _require_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    _validate_id(invoice_id, "Invoice id")
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")
    return invoice


def _require_payment(
    repository: payments_db.PaymentRepository,
    payment_id: int,
) -> payments_db.Payment:
    _validate_id(payment_id, "Payment id")
    payment = repository.get_by_id(payment_id)
    if payment is None:
        raise exceptions.NotFoundError(f"Payment not found (id={payment_id})")
    return payment


def _normalize_payment_date(payment_date: str) -> str:
    try:
        normalized = payments_db.normalize_payment_date(payment_date)
    except ValueError as e:
        raise _as_validation_error(e) from e

    if normalized > date.today().isoformat():
        raise exceptions.ValidationError("Payment date cannot be in the future.")

    return normalized


def _require_payable_invoice(invoice: sqlite3.Row) -> None:
    if invoice["status"] != "sent":
        raise exceptions.ConflictError("Only sent invoices can receive payments.")


def create_payment(
    cursor,
    invoice_id: int,
    amount_cents: int,
    payment_date: str,
    method: str,
    note: str | None = None,
) -> PaymentRecord:
    normalized_date = _normalize_payment_date(payment_date)
    repository = payments_db.PaymentRepository(cursor)

    try:
        with _payment_transaction(cursor):
            invoice = _require_invoice(cursor, invoice_id)
            _require_payable_invoice(invoice)

            summary = repository.get_payment_summary_for_invoice(invoice_id)
            amount_cents = payments_db.validate_payment_amount_cents(amount_cents)
            if amount_cents > summary.balance_due_cents:
                raise exceptions.ValidationError("Payment amount cannot exceed balance due.")

            payment = repository.create(
                payments_db.PaymentCreate(
                    invoice_id=invoice_id,
                    amount_cents=amount_cents,
                    payment_date=normalized_date,
                    method=method,
                    note=note,
                )
            )

            updated_summary = repository.get_payment_summary_for_invoice(invoice_id)
            if updated_summary.balance_due_cents == 0:
                updated = invoices_db.set_invoice_status(cursor, invoice_id, "paid")
                if not updated:
                    raise exceptions.ServiceError(f"Failed to mark invoice {invoice_id} as paid.")

    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid payment data.") from e

    return _to_payment_record(payment)


def get_payment_by_id(cursor, payment_id: int) -> PaymentRecord:
    repository = payments_db.PaymentRepository(cursor)
    return _to_payment_record(_require_payment(repository, payment_id))


def list_payments(cursor, invoice_id: int) -> list[PaymentRecord]:
    _require_invoice(cursor, invoice_id)
    repository = payments_db.PaymentRepository(cursor)
    return [
        _to_payment_record(payment)
        for payment in repository.list_by_invoice_id(invoice_id)
    ]


def get_payment_summary(cursor, invoice_id: int) -> PaymentSummaryRecord:
    _require_invoice(cursor, invoice_id)
    repository = payments_db.PaymentRepository(cursor)
    return _to_payment_summary_record(
        repository.get_payment_summary_for_invoice(invoice_id)
    )


def delete_payment(cursor, payment_id: int) -> None:
    repository = payments_db.PaymentRepository(cursor)

    try:
        with _payment_transaction(cursor):
            payment = repository.get_by_id(payment_id)
            if payment is None:
                raise exceptions.NotFoundError(f"Payment not found (id={payment_id})")

            invoice = invoices_db.get_invoice_by_id(cursor, payment.invoice_id)
            if invoice is None:
                raise exceptions.NotFoundError(f"Invoice not found (id={payment.invoice_id})")

            if invoice["status"] == "void":
                raise exceptions.ConflictError("Payments cannot be deleted from void invoices.")

            deleted = repository.delete(payment_id)
            if not deleted:
                raise exceptions.NotFoundError(f"Payment not found (id={payment_id})")

            updated_summary = repository.get_payment_summary_for_invoice(payment.invoice_id)

            if invoice["status"] == "paid" and updated_summary.balance_due_cents > 0:
                updated = invoices_db.set_invoice_status(cursor, payment.invoice_id, "sent")
                if not updated:
                    raise exceptions.ServiceError(
                        f"Failed to reopen invoice {payment.invoice_id} after payment deletion."
                    )

    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as exc:
        raise exceptions.ServiceError("Failed to delete payment.") from exc
    
