import pytest

from invoice_db.db import invoice_items, products
from invoice_db.db.products import ProductCreate
from invoice_db.services import exceptions
from invoice_db.services import invoices as invoice_services


def test_create_invoice_defaults_total_to_zero(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        date_issued=None,
        date_due=None,
    )

    assert invoice["total"] == 0


def test_create_invoice_rejects_manual_total(cursor, customer_john):
    with pytest.raises(exceptions.ValidationError):
        invoice_services.create_invoice(
            cursor,
            customer_id=customer_john,
            date_issued=None,
            date_due=None,
            total=1000,
        )


def test_update_invoice_rejects_manual_total(cursor, invoice_john):
    with pytest.raises(exceptions.ValidationError):
        invoice_services.update_invoice_by_id(
            cursor,
            invoice_id=invoice_john,
            new_total=1000,
        )


def test_set_invoice_status_rejects_inactive_line_item_product(cursor, invoice_john):
    product = products.create_product(
        cursor,
        ProductCreate(
            name="Widget",
            description="A test widget",
            unit_price_cents=1234,
        ),
    )
    repo = invoice_items.InvoiceItemRepository(cursor)
    repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product.id,
        )
    )
    products.update_product(cursor, product.id, is_active=False)

    with pytest.raises(exceptions.ValidationError) as exc:
        invoice_services.set_invoice_status(cursor, invoice_john, "sent")

    assert "inactive products" in str(exc.value)
    assert "Widget" in str(exc.value)
