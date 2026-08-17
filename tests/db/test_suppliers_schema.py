import sqlite3

import pytest

from invoice_db.db import products, suppliers
from invoice_db.db.products import ProductCreate
from invoice_db.db.suppliers import SupplierCreate


def test_suppliers_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'suppliers'"
    ).fetchone()

    assert row is not None


def test_suppliers_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(suppliers)").fetchall()
    }

    assert set(columns) == {
        "id",
        "name",
        "phone",
        "email",
        "website",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert columns["is_active"]["dflt_value"] == "1"


def test_suppliers_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(suppliers)").fetchall()
    }

    assert "idx_suppliers_name_nocase" in indexes
    assert "idx_suppliers_is_active" in indexes


def test_suppliers_reject_duplicate_names_case_insensitive(cursor):
    cursor.execute("INSERT INTO suppliers (name) VALUES (?)", ("Johnstone",))

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO suppliers (name) VALUES (?)", ("johnstone",))


def test_product_suppliers_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'product_suppliers'"
    ).fetchone()

    assert row is not None


def test_product_suppliers_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(product_suppliers)").fetchall()
    }

    assert set(columns) == {
        "product_id",
        "supplier_id",
        "note",
        "created_at",
        "updated_at",
    }


def test_product_suppliers_foreign_keys(cursor):
    foreign_keys = cursor.execute("PRAGMA foreign_key_list(product_suppliers)").fetchall()

    by_table = {row["table"]: row for row in foreign_keys}

    assert by_table["products"]["from"] == "product_id"
    assert by_table["products"]["on_delete"] == "CASCADE"
    assert by_table["suppliers"]["from"] == "supplier_id"
    assert by_table["suppliers"]["on_delete"] == "RESTRICT"


def test_product_suppliers_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(product_suppliers)").fetchall()
    }

    assert "idx_product_suppliers_product_id" in indexes
    assert "idx_product_suppliers_supplier_id" in indexes


def test_product_suppliers_reject_duplicate_product_supplier_pair(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    with pytest.raises(sqlite3.IntegrityError):
        suppliers.add_supplier_to_product(cursor, product.id, supplier.id)


def test_product_suppliers_cascade_when_product_deleted(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    cursor.execute("DELETE FROM products WHERE id = ?", (product.id,))

    row = cursor.execute(
        "SELECT * FROM product_suppliers WHERE product_id = ?",
        (product.id,),
    ).fetchone()
    assert row is None


def test_product_suppliers_restrict_when_supplier_has_products(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier.id,))
