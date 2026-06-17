import sqlite3

import pytest


def test_invoice_items_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'invoice_items'"
    ).fetchone()

    assert row is not None


def test_invoice_items_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(invoice_items)").fetchall()
    }

    assert set(columns) == {
        "id",
        "invoice_id",
        "product_id",
        "quantity",
        "unit_price",
        "created_at",
        "updated_at",
    }
    assert columns["quantity"]["dflt_value"] == "1"


def test_invoice_items_foreign_keys(cursor):
    foreign_keys = cursor.execute("PRAGMA foreign_key_list(invoice_items)").fetchall()

    by_table = {row["table"]: row for row in foreign_keys}

    assert by_table["invoices"]["from"] == "invoice_id"
    assert by_table["invoices"]["on_delete"] == "CASCADE"
    assert by_table["products"]["from"] == "product_id"
    assert by_table["products"]["on_delete"] == "RESTRICT"


def test_invoice_items_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(invoice_items)").fetchall()
    }

    assert "idx_invoice_items_invoice_id" in indexes
    assert "idx_invoice_items_product_id" in indexes
    assert "idx_invoice_items_invoice_product" in indexes


def test_invoice_items_reject_invalid_quantity(cursor, invoice_john):
    cursor.execute(
        """
        INSERT INTO products (name, unit_price)
        VALUES (?, ?)
        """,
        ("Widget", 1000),
    )
    product_id = cursor.lastrowid

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_john, product_id, 0, 1000),
        )
