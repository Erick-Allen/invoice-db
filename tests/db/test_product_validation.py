import pytest

from invoice_db.db import products
from invoice_db.db.products import ProductCreate


def test_create_product_empty_name_raises(cursor):
    with pytest.raises(ValueError):
        products.create_product(
            cursor,
            ProductCreate(name=" ", unit_price_cents=2500),
        )


def test_create_product_missing_unit_price_raises(cursor):
    with pytest.raises(ValueError):
        products.create_product(
            cursor,
            ProductCreate(name="Widget", unit_price_cents=None),
        )


def test_create_product_negative_unit_price_raises(cursor):
    with pytest.raises(ValueError):
        products.create_product(
            cursor,
            ProductCreate(name="Widget", unit_price_cents=-1),
        )


def test_create_product_non_integer_unit_price_raises(cursor):
    with pytest.raises(ValueError):
        products.create_product(
            cursor,
            ProductCreate(name="Widget", unit_price_cents="not-a-price"),
        )


def test_create_product_invalid_active_flag_raises(cursor):
    with pytest.raises(ValueError):
        products.create_product(
            cursor,
            ProductCreate(name="Widget", unit_price_cents=2500, is_active=2),
        )


def test_create_product_normalizes_description(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(
            name="Widget",
            description="  A   spaced   description  ",
            unit_price_cents=2500,
        ),
    )

    assert product.description == "A spaced description"


def test_create_product_empty_description_becomes_none(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", description="  ", unit_price_cents=2500),
    )

    assert product.description is None


def test_update_product_invalid_name_raises(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    with pytest.raises(ValueError):
        products.update_product(cursor, product.id, name=" ")


def test_update_product_negative_unit_price_raises(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    with pytest.raises(ValueError):
        products.update_product(cursor, product.id, unit_price_cents=-1)


def test_update_product_invalid_active_flag_raises(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    with pytest.raises(ValueError):
        products.update_product(cursor, product.id, is_active=2)
