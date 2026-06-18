from dataclasses import dataclass
from sqlite3 import Row

from invoice_db.utils import to_iso

from .invoices import get_invoice_by_id
from .validators import normalize_description


VALID_PAYMENT_METHODS = {"cash", "card", "check", "bank_transfer", "other"}


@dataclass
class PaymentCreate:
    invoice_id: int
    amount_cents: int
    payment_date: str
    method: str
    note: str | None = None


@dataclass
class Payment:
    id: int
    invoice_id: int
    amount_cents: int
    payment_date: str
    method: str
    note: str | None
    created_at: str
    updated_at: str


@dataclass
class PaymentSummary:
    invoice_id: int
    invoice_total_cents: int
    amount_paid_cents: int
    balance_due_cents: int
    is_paid: bool


def validate_payment_amount_cents(amount_cents: int) -> int:
    if amount_cents is None:
        raise ValueError("Payment amount is required.")
    try:
        amount_cents = int(amount_cents)
    except (TypeError, ValueError):
        raise ValueError("Payment amount must be a valid integer.")
    if amount_cents <= 0:
        raise ValueError("Payment amount must be greater than 0.")
    return amount_cents


def normalize_payment_method(method: str) -> str:
    if not method or not isinstance(method, str):
        raise ValueError("Payment method is required.")
    method = method.strip().lower()
    if method not in VALID_PAYMENT_METHODS:
        allowed = ", ".join(sorted(VALID_PAYMENT_METHODS))
        raise ValueError(f"Payment method must be one of: {allowed}.")
    return method


def normalize_payment_date(payment_date: str) -> str:
    if not payment_date or not isinstance(payment_date, str):
        raise ValueError("Payment date is required.")
    return to_iso(payment_date)


def _to_payment(row: Row) -> Payment:
    return Payment(
        id=row["id"],
        invoice_id=row["invoice_id"],
        amount_cents=row["amount_cents"],
        payment_date=row["payment_date"],
        method=row["method"],
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PaymentRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def create(self, payment: PaymentCreate) -> Payment:
        self._require_invoice(payment.invoice_id)
        amount_cents = validate_payment_amount_cents(payment.amount_cents)
        payment_date = normalize_payment_date(payment.payment_date)
        method = normalize_payment_method(payment.method)
        note = normalize_description(payment.note)

        self.cursor.execute("""
            INSERT INTO payments (invoice_id, amount_cents, payment_date, method, note)
            VALUES (?, ?, ?, ?, ?)
        """, (payment.invoice_id, amount_cents, payment_date, method, note))

        created_payment = self.get_by_id(self.cursor.lastrowid)
        if created_payment is None:
            raise RuntimeError("Payment was created but could not be retrieved.")
        return created_payment

    def get_by_id(self, payment_id: int) -> Payment | None:
        self.cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        row = self.cursor.fetchone()
        return _to_payment(row) if row else None

    def list_by_invoice_id(self, invoice_id: int) -> list[Payment]:
        self.cursor.execute("""
            SELECT *
            FROM payments
            WHERE invoice_id = ?
            ORDER BY payment_date DESC, id DESC
        """, (invoice_id,))
        return [_to_payment(row) for row in self.cursor.fetchall()]

    def delete(self, payment_id: int) -> bool:
        self.cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        return self.cursor.rowcount > 0

    def sum_payments_for_invoice(self, invoice_id: int) -> int:
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount_cents), 0) AS total
            FROM payments
            WHERE invoice_id = ?
        """, (invoice_id,))
        row = self.cursor.fetchone()
        return row["total"] if row else 0

    def get_payment_summary_for_invoice(self, invoice_id: int) -> PaymentSummary:
        invoice = self._require_invoice(invoice_id)
        amount_paid_cents = self.sum_payments_for_invoice(invoice_id)
        invoice_total_cents = invoice["total"]
        balance_due_cents = invoice_total_cents - amount_paid_cents

        return PaymentSummary(
            invoice_id=invoice_id,
            invoice_total_cents=invoice_total_cents,
            amount_paid_cents=amount_paid_cents,
            balance_due_cents=balance_due_cents,
            is_paid=balance_due_cents == 0,
        )

    def _require_invoice(self, invoice_id: int) -> Row:
        invoice = get_invoice_by_id(self.cursor, invoice_id)
        if invoice is None:
            raise ValueError(f"Invoice not found (id={invoice_id})")
        return invoice
