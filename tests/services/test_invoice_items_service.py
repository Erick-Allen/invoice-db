import pytest

from invoice_db.db import invoices, products
from invoice_db.db.products import ProductCreate
from invoice_db.services import exceptions
from invoice_db.services import invoice_items as invoice_item_services


def lock_invoice(cursor, invoice_id: int, status: str) -> None:
    cursor.execute(
        """
        UPDATE invoices
        SET status = ?, date_due = COALESCE(date_due, date_issued)
        WHERE id = ?
        """,
        (status, invoice_id),
    )


@pytest.fixture
def product_widget(cursor):
    return products.create_product(
        cursor,
        ProductCreate(
            name="Widget",
            description="A test widget",
            unit_price_cents=2500,
        ),
    )


@pytest.fixture
def product_service(cursor):
    return products.create_product(
        cursor,
        ProductCreate(
            name="Service",
            description="A test service",
            unit_price_cents=4000,
        ),
    )


def test_create_invoice_item_recalculates_invoice_total(cursor, invoice_john, product_widget):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
        quantity=2,
    )

    invoice = invoices.get_invoice_by_id(cursor, invoice_john)

    assert item["line_total_cents"] == 5000
    assert invoice["total"] == 5000


@pytest.mark.parametrize("status", ["sent", "paid", "void"])
def test_create_invoice_item_rejects_locked_invoice(cursor, invoice_john, product_widget, status):
    lock_invoice(cursor, invoice_john, status)

    with pytest.raises(exceptions.ConflictError):
        invoice_item_services.create_invoice_item(
            cursor,
            invoice_id=invoice_john,
            product_id=product_widget.id,
        )


@pytest.mark.parametrize("status", ["sent", "paid", "void"])
def test_update_invoice_item_rejects_locked_invoice(cursor, invoice_john, product_widget, status):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )
    lock_invoice(cursor, invoice_john, status)

    with pytest.raises(exceptions.ConflictError):
        invoice_item_services.update_invoice_item_by_id(cursor, item["id"], quantity=2)


@pytest.mark.parametrize("status", ["sent", "paid", "void"])
def test_delete_invoice_item_rejects_locked_invoice(cursor, invoice_john, product_widget, status):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )
    lock_invoice(cursor, invoice_john, status)

    with pytest.raises(exceptions.ConflictError):
        invoice_item_services.delete_invoice_item(cursor, item["id"])


def test_create_invoice_item_rejects_inactive_product(cursor, invoice_john, product_widget):
    products.update_product(cursor, product_widget.id, is_active=False)

    with pytest.raises(exceptions.ValidationError):
        invoice_item_services.create_invoice_item(
            cursor,
            invoice_id=invoice_john,
            product_id=product_widget.id,
        )


def test_update_existing_invoice_item_allows_inactive_product(cursor, invoice_john, product_widget):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )
    products.update_product(cursor, product_widget.id, is_active=False)

    updated = invoice_item_services.update_invoice_item_by_id(cursor, item["id"], quantity=3)

    assert updated["quantity"] == 3
    assert updated["line_total_cents"] == 7500


def test_update_invoice_item_product_resets_unit_price(
    cursor,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
        quantity=2,
    )

    updated = invoice_item_services.update_invoice_item_by_id(
        cursor,
        item["id"],
        product_id=product_service.id,
    )

    assert updated["product_id"] == product_service.id
    assert updated["unit_price_cents"] == 4000
    assert updated["line_total_cents"] == 8000


def test_update_invoice_item_product_allows_unit_price_override(
    cursor,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
        quantity=2,
    )

    updated = invoice_item_services.update_invoice_item_by_id(
        cursor,
        item["id"],
        product_id=product_service.id,
        unit_price_cents=4500,
    )

    assert updated["product_id"] == product_service.id
    assert updated["unit_price_cents"] == 4500
    assert updated["line_total_cents"] == 9000


def test_update_invoice_item_rejects_inactive_replacement_product(
    cursor,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )
    products.update_product(cursor, product_service.id, is_active=False)

    with pytest.raises(exceptions.ValidationError):
        invoice_item_services.update_invoice_item_by_id(
            cursor,
            item["id"],
            product_id=product_service.id,
        )


def test_update_invoice_item_rejects_missing_replacement_product(cursor, invoice_john, product_widget):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )

    with pytest.raises(exceptions.NotFoundError):
        invoice_item_services.update_invoice_item_by_id(
            cursor,
            item["id"],
            product_id=9999,
        )


def test_list_invoice_items_requires_existing_invoice(cursor):
    with pytest.raises(exceptions.NotFoundError):
        invoice_item_services.list_invoice_items(cursor, invoice_id=9999)


def test_get_invoice_item_requires_existing_item(cursor):
    with pytest.raises(exceptions.NotFoundError):
        invoice_item_services.get_invoice_item_by_id(cursor, invoice_item_id=9999)


def test_update_invoice_item_requires_changes(cursor, invoice_john, product_widget):
    item = invoice_item_services.create_invoice_item(
        cursor,
        invoice_id=invoice_john,
        product_id=product_widget.id,
    )

    with pytest.raises(exceptions.ValidationError):
        invoice_item_services.update_invoice_item_by_id(cursor, item["id"])
