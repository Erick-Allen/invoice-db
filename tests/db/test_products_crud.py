from invoice_db.db import products
from invoice_db.db.products import ProductCreate


def test_create_product(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(
            name="Widget",
            description="A test widget",
            unit_price_cents=2500,
        ),
    )

    row = cursor.execute("SELECT * FROM products WHERE id = ?", (product.id,)).fetchone()

    assert row is not None
    assert product.id == row["id"]
    assert product.name == "Widget"
    assert product.description == "A test widget"
    assert product.unit_price_cents == 2500
    assert product.is_active is True


def test_get_product_by_id(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    result = products.get_product_by_id(cursor, product.id)

    assert result == product


def test_get_products(cursor):
    first = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )
    second = products.create_product(
        cursor,
        ProductCreate(name="Service", unit_price_cents=5000),
    )

    result = products.get_products(cursor)

    assert [product.id for product in result] == [first.id, second.id]


def test_get_products_active_only(cursor):
    active = products.create_product(
        cursor,
        ProductCreate(name="Active Widget", unit_price_cents=2500),
    )
    inactive = products.create_product(
        cursor,
        ProductCreate(name="Inactive Widget", unit_price_cents=5000, is_active=False),
    )

    result = products.get_products(cursor, active_only=True)

    assert [product.id for product in result] == [active.id]
    assert inactive.id not in {product.id for product in result}


def test_update_product_name_description_price_and_active_flag(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", description="Old", unit_price_cents=2500),
    )

    updated = products.update_product(
        cursor,
        product.id,
        name="Updated Widget",
        description="Updated",
        unit_price_cents=3000,
        is_active=False,
    )

    assert updated.id == product.id
    assert updated.name == "Updated Widget"
    assert updated.description == "Updated"
    assert updated.unit_price_cents == 3000
    assert updated.is_active is False


def test_update_product_no_fields_returns_existing_product(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    updated = products.update_product(cursor, product.id)

    assert updated == product


def test_update_missing_product_returns_none(cursor):
    assert products.update_product(cursor, 9999, name="Missing") is None


def test_delete_product(cursor):
    product = products.create_product(
        cursor,
        ProductCreate(name="Widget", unit_price_cents=2500),
    )

    deleted = products.delete_product(cursor, product.id)

    assert deleted is True
    assert products.get_product_by_id(cursor, product.id) is None


def test_delete_missing_product_returns_false(cursor):
    assert products.delete_product(cursor, 9999) is False


def test_assert_product_exists_raises_for_missing_product(cursor):
    try:
        products.assert_product_exists(cursor, 9999)
    except ValueError as error:
        assert str(error) == "Product not found (id=9999)"
    else:
        raise AssertionError("Expected missing product to raise ValueError")
