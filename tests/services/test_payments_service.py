from datetime import date, timedelta

import pytest

from invoice_db.db import invoices, payments
from invoice_db.services import exceptions
from invoice_db.services import payments as payment_services


TODAY = date.today().isoformat()


def set_invoice_status(cursor, invoice_id: int, status: str) -> None:
    cursor.execute(
        """
        UPDATE invoices
        SET status = ?, date_due = COALESCE(date_due, date_issued)
        WHERE id = ?
        """,
        (status, invoice_id),
    )


def test_create_payment_on_sent_invoice_keeps_partial_payment_sent(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")

    payment = payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=1000,
        payment_date=TODAY,
        method="cash",
    )

    invoice = invoices.get_invoice_by_id(cursor, invoice_john)

    assert payment["amount_cents"] == 1000
    assert invoice["status"] == "sent"


def test_create_payment_marks_invoice_paid_when_balance_is_fully_paid(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")

    payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=123400,
        payment_date=TODAY,
        method="card",
    )

    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    summary = payment_services.get_payment_summary(cursor, invoice_john)

    assert invoice["status"] == "paid"
    assert summary["amount_paid_cents"] == 123400
    assert summary["balance_due_cents"] == 0
    assert summary["is_paid"] is True


@pytest.mark.parametrize("status", ["draft", "paid", "void"])
def test_create_payment_rejects_non_sent_invoice(cursor, invoice_john, status):
    set_invoice_status(cursor, invoice_john, status)

    with pytest.raises(exceptions.ConflictError):
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date=TODAY,
            method="cash",
        )


@pytest.mark.parametrize("amount", [0, -1])
def test_create_payment_rejects_non_positive_amount(cursor, invoice_john, amount):
    set_invoice_status(cursor, invoice_john, "sent")

    with pytest.raises(exceptions.ValidationError):
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=amount,
            payment_date=TODAY,
            method="cash",
        )


def test_create_payment_rejects_future_payment_date(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")
    future_date = (date.today() + timedelta(days=1)).isoformat()

    with pytest.raises(exceptions.ValidationError) as exc:
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date=future_date,
            method="cash",
        )

    assert "future" in str(exc.value)


def test_create_payment_rejects_invalid_method(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")

    with pytest.raises(exceptions.ValidationError):
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date=TODAY,
            method="crypto",
        )


def test_create_payment_rejects_overpayment(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")

    with pytest.raises(exceptions.ValidationError) as exc:
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=123401,
            payment_date=TODAY,
            method="cash",
        )

    assert "balance due" in str(exc.value)


def test_create_payment_requires_existing_invoice(cursor):
    with pytest.raises(exceptions.NotFoundError):
        payment_services.create_payment(
            cursor,
            invoice_id=9999,
            amount_cents=1000,
            payment_date=TODAY,
            method="cash",
        )


def test_get_and_list_payments(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")
    created = payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=1000,
        payment_date=TODAY,
        method="cash",
    )

    assert payment_services.get_payment_by_id(cursor, created["id"]) == created
    assert payment_services.list_payments(cursor, invoice_john) == [created]


def test_get_missing_payment_raises_not_found(cursor):
    with pytest.raises(exceptions.NotFoundError):
        payment_services.get_payment_by_id(cursor, 9999)


def test_payment_summary_requires_existing_invoice(cursor):
    with pytest.raises(exceptions.NotFoundError):
        payment_services.get_payment_summary(cursor, 9999)


def test_delete_payment_from_sent_invoice(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")
    created = payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=1000,
        payment_date=TODAY,
        method="cash",
    )

    payment_services.delete_payment(cursor, created["id"])

    assert payment_services.list_payments(cursor, invoice_john) == []
    assert invoices.get_invoice_by_id(cursor, invoice_john)["status"] == "sent"


def test_delete_payment_from_paid_invoice_reopens_to_sent(cursor, invoice_john):
    set_invoice_status(cursor, invoice_john, "sent")
    created = payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=123400,
        payment_date=TODAY,
        method="cash",
    )
    assert invoices.get_invoice_by_id(cursor, invoice_john)["status"] == "paid"

    payment_services.delete_payment(cursor, created["id"])

    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    summary = payment_services.get_payment_summary(cursor, invoice_john)

    assert invoice["status"] == "sent"
    assert summary["amount_paid_cents"] == 0
    assert summary["balance_due_cents"] == 123400


def test_delete_payment_from_void_invoice_fails(cursor, invoice_john):
    repo = payments.PaymentRepository(cursor)
    created = repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date=TODAY,
            method="cash",
        )
    )
    set_invoice_status(cursor, invoice_john, "void")

    with pytest.raises(exceptions.ConflictError):
        payment_services.delete_payment(cursor, created.id)

    assert repo.get_by_id(created.id) is not None


def test_create_payment_rolls_back_if_paid_status_update_fails(cursor, invoice_john, monkeypatch):
    set_invoice_status(cursor, invoice_john, "sent")

    monkeypatch.setattr(
        payment_services.invoices_db,
        "set_invoice_status",
        lambda *args, **kwargs: False,
    )

    with pytest.raises(exceptions.ServiceError):
        payment_services.create_payment(
            cursor,
            invoice_id=invoice_john,
            amount_cents=123400,
            payment_date=TODAY,
            method="cash",
        )

    assert payment_services.list_payments(cursor, invoice_john) == []
    assert invoices.get_invoice_by_id(cursor, invoice_john)["status"] == "sent"


def test_delete_payment_rolls_back_if_reopen_status_update_fails(cursor, invoice_john, monkeypatch):
    set_invoice_status(cursor, invoice_john, "sent")
    created = payment_services.create_payment(
        cursor,
        invoice_id=invoice_john,
        amount_cents=123400,
        payment_date=TODAY,
        method="cash",
    )
    monkeypatch.setattr(
        payment_services.invoices_db,
        "set_invoice_status",
        lambda *args, **kwargs: False,
    )

    with pytest.raises(exceptions.ServiceError):
        payment_services.delete_payment(cursor, created["id"])

    assert payment_services.get_payment_by_id(cursor, created["id"]) == created
    assert invoices.get_invoice_by_id(cursor, invoice_john)["status"] == "paid"
