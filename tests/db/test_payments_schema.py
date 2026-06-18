import sqlite3

import pytest

from invoice_db.db.payments import VALID_PAYMENT_METHODS


def test_payments_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'payments'"
    ).fetchone()

    assert row is not None


def test_payments_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(payments)").fetchall()
    }

    assert set(columns) == {
        "id",
        "invoice_id",
        "amount_cents",
        "payment_date",
        "method",
        "note",
        "created_at",
        "updated_at",
    }
    assert columns["invoice_id"]["notnull"] == 1
    assert columns["amount_cents"]["notnull"] == 1
    assert columns["payment_date"]["notnull"] == 1
    assert columns["method"]["notnull"] == 1


def test_payments_foreign_keys(cursor):
    foreign_keys = cursor.execute("PRAGMA foreign_key_list(payments)").fetchall()

    assert len(foreign_keys) == 1
    assert foreign_keys[0]["table"] == "invoices"
    assert foreign_keys[0]["from"] == "invoice_id"
    assert foreign_keys[0]["on_delete"] == "CASCADE"


def test_payments_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(payments)").fetchall()
    }

    assert "idx_payments_invoice_id" in indexes
    assert "idx_payments_payment_date" in indexes
    assert "idx_payments_method" in indexes


@pytest.mark.parametrize("method", sorted(VALID_PAYMENT_METHODS))
def test_payments_accept_valid_methods(cursor, invoice_john, method):
    cursor.execute(
        """
        INSERT INTO payments (invoice_id, amount_cents, payment_date, method)
        VALUES (?, ?, ?, ?)
        """,
        (invoice_john, 1000, "2026-06-17", method),
    )

    assert cursor.lastrowid is not None


def test_payments_reject_invalid_method(cursor, invoice_john):
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO payments (invoice_id, amount_cents, payment_date, method)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_john, 1000, "2026-06-17", "crypto"),
        )


@pytest.mark.parametrize("amount", [0, -1])
def test_payments_reject_non_positive_amount(cursor, invoice_john, amount):
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO payments (invoice_id, amount_cents, payment_date, method)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_john, amount, "2026-06-17", "cash"),
        )


def test_payments_reject_blank_payment_date(cursor, invoice_john):
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO payments (invoice_id, amount_cents, payment_date, method)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_john, 1000, "", "cash"),
        )


def test_payments_delete_when_invoice_is_deleted(cursor, invoice_john):
    cursor.execute(
        """
        INSERT INTO payments (invoice_id, amount_cents, payment_date, method)
        VALUES (?, ?, ?, ?)
        """,
        (invoice_john, 1000, "2026-06-17", "cash"),
    )

    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_john,))

    row = cursor.execute("SELECT * FROM payments WHERE invoice_id = ?", (invoice_john,)).fetchone()
    assert row is None
