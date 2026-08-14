import pytest
import sqlite3

from invoice_db.db import product_categories, products
from invoice_db.db.product_categories import ProductCategoryCreate
from invoice_db.db.products import ProductCreate


def test_default_product_category_is_seeded(cursor):
    category = product_categories.get_product_category_by_id(cursor, 1)

    assert category is not None
    assert category.name == "Uncategorized"
    assert category.is_active is True


def test_create_product_category(cursor):
    category = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(
            name="Labor",
            description="Billable labor",
        ),
    )

    assert category.id > 1
    assert category.name == "Labor"
    assert category.description == "Billable labor"
    assert category.is_active is True


def test_product_category_names_are_case_insensitive_unique(cursor):
    product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Labor"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        product_categories.create_product_category(
            cursor,
            ProductCategoryCreate(name="labor"),
        )


def test_get_product_categories_active_only(cursor):
    active = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Labor"),
    )
    inactive = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Archived", is_active=False),
    )

    result = product_categories.get_product_categories(cursor, active_only=True)

    assert active.id in {category.id for category in result}
    assert inactive.id not in {category.id for category in result}


def test_create_product_defaults_to_uncategorized(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    assert product.category_id == product_categories.DEFAULT_CATEGORY_ID


def test_create_product_with_category(cursor):
    category = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Materials"),
    )

    product = products.create_product(
        cursor,
        ProductCreate(
            name="Cable",
            unit_price_cents=1200,
            category_id=category.id,
        ),
    )

    assert product.category_id == category.id


def test_update_product_category(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )
    category = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Labor"),
    )

    updated = products.update_product(cursor, product.id, category_id=category.id)

    assert updated.category_id == category.id


def test_delete_category_with_products_is_restricted(cursor):
    category = product_categories.create_product_category(
        cursor,
        ProductCategoryCreate(name="Materials"),
    )
    products.create_product(
        cursor,
        ProductCreate(name="Cable", unit_price_cents=1200, category_id=category.id),
    )

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM product_categories WHERE id = ?", (category.id,))
