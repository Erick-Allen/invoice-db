import pytest

from invoice_db.db import payments


@pytest.fixture
def payment_repo(cursor):
    return payments.PaymentRepository(cursor)


def test_create_payment_normalizes_method_and_note(payment_repo, invoice_john):
    payment = payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=2500,
            payment_date="2026-06-17",
            method=" CASH ",
            note="  First   payment  ",
        )
    )

    assert payment.invoice_id == invoice_john
    assert payment.amount_cents == 2500
    assert payment.payment_date == "2026-06-17"
    assert payment.method == "cash"
    assert payment.note == "First payment"


def test_get_payment_by_id_returns_payment(payment_repo, invoice_john):
    payment = payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=2500,
            payment_date="2026-06-17",
            method="card",
        )
    )

    result = payment_repo.get_by_id(payment.id)

    assert result == payment


def test_get_missing_payment_returns_none(payment_repo):
    assert payment_repo.get_by_id(9999) is None


def test_list_by_invoice_id_returns_payments(payment_repo, invoice_john):
    first = payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date="2026-06-17",
            method="cash",
        )
    )
    second = payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=2000,
            payment_date="2026-06-18",
            method="check",
        )
    )

    assert payment_repo.list_by_invoice_id(invoice_john) == [second, first]


def test_delete_payment(payment_repo, invoice_john):
    payment = payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=2500,
            payment_date="2026-06-17",
            method="bank_transfer",
        )
    )

    assert payment_repo.delete(payment.id) is True
    assert payment_repo.get_by_id(payment.id) is None


def test_delete_missing_payment_returns_false(payment_repo):
    assert payment_repo.delete(9999) is False


def test_sum_payments_for_invoice(payment_repo, invoice_john):
    payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date="2026-06-17",
            method="cash",
        )
    )
    payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=2000,
            payment_date="2026-06-18",
            method="card",
        )
    )

    assert payment_repo.sum_payments_for_invoice(invoice_john) == 3000


def test_payment_summary_for_invoice(payment_repo, invoice_john):
    payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=1000,
            payment_date="2026-06-17",
            method="cash",
        )
    )

    summary = payment_repo.get_payment_summary_for_invoice(invoice_john)

    assert summary.invoice_id == invoice_john
    assert summary.invoice_total_cents == 123400
    assert summary.amount_paid_cents == 1000
    assert summary.balance_due_cents == 122400
    assert summary.is_paid is False


def test_paid_payment_summary(payment_repo, invoice_john):
    payment_repo.create(
        payments.PaymentCreate(
            invoice_id=invoice_john,
            amount_cents=123400,
            payment_date="2026-06-17",
            method="other",
        )
    )

    summary = payment_repo.get_payment_summary_for_invoice(invoice_john)

    assert summary.amount_paid_cents == 123400
    assert summary.balance_due_cents == 0
    assert summary.is_paid is True


def test_create_payment_rejects_missing_invoice(payment_repo):
    with pytest.raises(ValueError):
        payment_repo.create(
            payments.PaymentCreate(
                invoice_id=9999,
                amount_cents=2500,
                payment_date="2026-06-17",
                method="cash",
            )
        )


@pytest.mark.parametrize("amount", [0, -1])
def test_create_payment_rejects_invalid_amount(payment_repo, invoice_john, amount):
    with pytest.raises(ValueError):
        payment_repo.create(
            payments.PaymentCreate(
                invoice_id=invoice_john,
                amount_cents=amount,
                payment_date="2026-06-17",
                method="cash",
            )
        )


def test_create_payment_rejects_invalid_method(payment_repo, invoice_john):
    with pytest.raises(ValueError):
        payment_repo.create(
            payments.PaymentCreate(
                invoice_id=invoice_john,
                amount_cents=2500,
                payment_date="2026-06-17",
                method="crypto",
            )
        )


def test_payment_summary_rejects_missing_invoice(payment_repo):
    with pytest.raises(ValueError):
        payment_repo.get_payment_summary_for_invoice(9999)
