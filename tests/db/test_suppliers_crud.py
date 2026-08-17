import sqlite3

import pytest

from invoice_db.db import products, suppliers
from invoice_db.db.products import ProductCreate
from invoice_db.db.suppliers import SupplierCreate


def create_product(cursor, name="Widget"):
    return products.create_product(
        cursor,
        ProductCreate(name=name, unit_price_cents=2500),
    )


def test_create_supplier(cursor):
    supplier = suppliers.create_supplier(
        cursor,
        SupplierCreate(
            name="  Johnstone  Supply ",
            phone="  555-0100 ",
            email=" source@example.com ",
            website=" https://example.com ",
        ),
    )

    assert supplier.id > 0
    assert supplier.name == "Johnstone Supply"
    assert supplier.phone == "555-0100"
    assert supplier.email == "source@example.com"
    assert supplier.website == "https://example.com"
    assert supplier.is_active is True


def test_get_supplier_by_name_is_case_insensitive(cursor):
    created = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))

    result = suppliers.get_supplier_by_name(cursor, "johnstone")

    assert result is not None
    assert result.id == created.id


def test_get_suppliers_active_only(cursor):
    active = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    inactive = suppliers.create_supplier(
        cursor,
        SupplierCreate(name="Archived Supplier", is_active=False),
    )

    result = suppliers.get_suppliers(cursor, active_only=True)

    assert active.id in {supplier.id for supplier in result}
    assert inactive.id not in {supplier.id for supplier in result}


def test_update_supplier(cursor):
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))

    updated = suppliers.update_supplier(
        cursor,
        supplier.id,
        name="Home Depot",
        phone="555-0111",
        email="desk@example.com",
        website="https://homedepot.example",
        is_active=False,
    )

    assert updated is not None
    assert updated.id == supplier.id
    assert updated.name == "Home Depot"
    assert updated.phone == "555-0111"
    assert updated.email == "desk@example.com"
    assert updated.website == "https://homedepot.example"
    assert updated.is_active is False


def test_update_supplier_no_fields_returns_existing_supplier(cursor):
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))

    updated = suppliers.update_supplier(cursor, supplier.id)

    assert updated == supplier


def test_delete_supplier(cursor):
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))

    assert suppliers.delete_supplier(cursor, supplier.id) is True
    assert suppliers.get_supplier_by_id(cursor, supplier.id) is None


def test_delete_missing_supplier_returns_false(cursor):
    assert suppliers.delete_supplier(cursor, 9999) is False


def test_add_and_list_product_supplier(cursor):
    product = create_product(cursor)
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))

    product_supplier = suppliers.add_supplier_to_product(
        cursor,
        product.id,
        supplier.id,
        note="Usually stocked locally",
    )
    result = suppliers.get_suppliers_for_product(cursor, product.id)

    assert product_supplier.product_id == product.id
    assert product_supplier.supplier_id == supplier.id
    assert product_supplier.note == "Usually stocked locally"
    assert [supplier.name for supplier in result] == ["Johnstone"]


def test_get_products_for_supplier(cursor):
    first = create_product(cursor, name="Widget")
    second = create_product(cursor, name="Cable")
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, first.id, supplier.id)
    suppliers.add_supplier_to_product(cursor, second.id, supplier.id)

    result = suppliers.get_products_for_supplier(cursor, supplier.id)

    assert [product.name for product in result] == ["Cable", "Widget"]


def test_update_product_supplier_note(cursor):
    product = create_product(cursor)
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    updated = suppliers.update_product_supplier_note(
        cursor,
        product.id,
        supplier.id,
        "Counter pickup",
    )

    assert updated is not None
    assert updated.note == "Counter pickup"


def test_remove_supplier_from_product(cursor):
    product = create_product(cursor)
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    assert suppliers.remove_supplier_from_product(cursor, product.id, supplier.id) is True
    assert suppliers.get_suppliers_for_product(cursor, product.id) == []


def test_remove_supplier_from_all_products(cursor):
    first = create_product(cursor, name="Widget")
    second = create_product(cursor, name="Cable")
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, first.id, supplier.id)
    suppliers.add_supplier_to_product(cursor, second.id, supplier.id)

    removed_count = suppliers.remove_supplier_from_all_products(cursor, supplier.id)

    assert removed_count == 2
    assert suppliers.count_products_for_supplier(cursor, supplier.id) == 0


def test_delete_supplier_with_products_is_restricted(cursor):
    product = create_product(cursor)
    supplier = suppliers.create_supplier(cursor, SupplierCreate(name="Johnstone"))
    suppliers.add_supplier_to_product(cursor, product.id, supplier.id)

    with pytest.raises(sqlite3.IntegrityError):
        suppliers.delete_supplier(cursor, supplier.id)
