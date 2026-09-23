import pytest
from datetime import date, timedelta

from invoice_db.db import invoice_items, products
from invoice_db.db import invoices as invoices_db
from invoice_db.db.products import ProductCreate
from invoice_db.services import customer_locations, exceptions
from invoice_db.services import invoices as invoice_services


def test_create_invoice_defaults_total_to_zero(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        date_issued=None,
        date_due=None,
    )

    assert invoice["total"] == 0
    assert invoice["location_id"] is None


def test_create_invoice_with_title(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        title="Maintenance visit",
        date_issued=None,
        date_due=None,
    )

    assert invoice["title"] == "Maintenance visit"


def test_create_invoice_with_description(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        description="Installed mini split in upstairs bedroom.",
        date_issued=None,
        date_due=None,
    )

    assert invoice["description"] == "Installed mini split in upstairs bedroom."


def test_create_invoice_with_customer_location(cursor, customer_john):
    location = customer_locations.create_customer_location(
        cursor,
        customer_id=customer_john,
        label="Home",
        address_line1="123 Main St",
        city="Orlando",
        state="FL",
        postal_code="32801",
    )

    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        location_id=location["id"],
        date_issued=None,
        date_due=None,
    )

    assert invoice["location_id"] == location["id"]


def test_create_invoice_rejects_location_for_different_customer(cursor, customer_john, customer_alice):
    location = customer_locations.create_customer_location(
        cursor,
        customer_id=customer_alice,
        label="Office",
        address_line1="456 Office Rd",
        city="Orlando",
        state="FL",
        postal_code="32801",
    )

    with pytest.raises(exceptions.ValidationError, match="does not belong"):
        invoice_services.create_invoice(
            cursor,
            customer_id=customer_john,
            location_id=location["id"],
            date_issued=None,
            date_due=None,
        )


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


def test_update_invoice_location(cursor, customer_john, invoice_john):
    location = customer_locations.create_customer_location(
        cursor,
        customer_id=customer_john,
        label="Home",
        address_line1="123 Main St",
        city="Orlando",
        state="FL",
        postal_code="32801",
    )

    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_location_id=location["id"],
        update_location=True,
    )

    assert invoice["location_id"] == location["id"]


def test_update_invoice_title(cursor, invoice_john):
    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_title="Mini split install",
        update_title=True,
    )

    assert invoice["title"] == "Mini split install"


def test_update_invoice_can_clear_title(cursor, invoice_john):
    invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_title="Mini split install",
        update_title=True,
    )

    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_title=None,
        update_title=True,
    )

    assert invoice["title"] is None


def test_update_invoice_description(cursor, invoice_john):
    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_description="Replaced capacitor and verified system pressures.",
        update_description=True,
    )

    assert invoice["description"] == "Replaced capacitor and verified system pressures."


def test_update_invoice_can_clear_description(cursor, invoice_john):
    invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_description="Replaced capacitor and verified system pressures.",
        update_description=True,
    )

    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_description=None,
        update_description=True,
    )

    assert invoice["description"] is None


def test_update_invoice_can_clear_location(cursor, customer_john, invoice_john):
    location = customer_locations.create_customer_location(
        cursor,
        customer_id=customer_john,
        label="Home",
        address_line1="123 Main St",
        city="Orlando",
        state="FL",
        postal_code="32801",
    )
    invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_location_id=location["id"],
        update_location=True,
    )

    invoice = invoice_services.update_invoice_by_id(
        cursor,
        invoice_id=invoice_john,
        new_location_id=None,
        update_location=True,
    )

    assert invoice["location_id"] is None


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


def test_set_invoice_status_draft_to_sent_autofills_dates(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        date_issued=None,
        date_due=None,
    )

    updated_invoice = invoice_services.set_invoice_status(cursor, invoice["id"], "sent")

    assert updated_invoice["status"] == "sent"
    assert updated_invoice["date_issued"] == date.today().isoformat()
    assert updated_invoice["date_due"] == (date.today() + timedelta(days=30)).isoformat()


def test_set_invoice_status_draft_to_sent_preserves_existing_draft_dates(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        date_issued="01/01/2100",
        date_due="02/01/2100",
    )

    updated_invoice = invoice_services.set_invoice_status(cursor, invoice["id"], "sent")

    assert updated_invoice["status"] == "sent"
    assert updated_invoice["date_issued"] == "2100-01-01"
    assert updated_invoice["date_due"] == "2100-02-01"


def test_set_invoice_status_draft_to_sent_fills_missing_issue_date_and_preserves_due_date(cursor, customer_john):
    invoice = invoice_services.create_invoice(
        cursor,
        customer_id=customer_john,
        date_issued=None,
        date_due="01/01/2100",
    )

    updated_invoice = invoice_services.set_invoice_status(cursor, invoice["id"], "sent")

    assert updated_invoice["status"] == "sent"
    assert updated_invoice["date_issued"] == date.today().isoformat()
    assert updated_invoice["date_due"] == "2100-01-01"


def test_set_invoice_status_rejects_manual_sent_to_paid(cursor, invoice_john):
    invoice_services.set_invoice_status(cursor, invoice_john, "sent")

    with pytest.raises(exceptions.ValidationError):
        invoice_services.set_invoice_status(cursor, invoice_john, "paid")


def test_set_invoice_status_rejects_manual_paid_to_sent(cursor, invoice_john):
    invoice_services.set_invoice_status(cursor, invoice_john, "sent")
    invoices_db.set_invoice_status(cursor, invoice_john, "paid")

    with pytest.raises(exceptions.ValidationError):
        invoice_services.set_invoice_status(cursor, invoice_john, "sent")


def test_set_invoice_status_rejects_manual_paid_to_void(cursor, invoice_john):
    invoice_services.set_invoice_status(cursor, invoice_john, "sent")
    invoices_db.set_invoice_status(cursor, invoice_john, "paid")

    with pytest.raises(exceptions.ValidationError):
        invoice_services.set_invoice_status(cursor, invoice_john, "void")
