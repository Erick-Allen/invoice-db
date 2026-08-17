import pytest

from invoice_db.db import invoice_items, invoices, products
from invoice_db.db.products import ProductCreate


@pytest.fixture
def product_widget(cursor):
    return products.create_product(
        cursor,
        ProductCreate(
            name="Widget",
            description="A test widget",
            cost_cents=1000,
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
            cost_cents=1500,
            unit_price_cents=4000,
        ),
    )


@pytest.fixture
def invoice_item_repo(cursor):
    return invoice_items.InvoiceItemRepository(cursor)


def test_create_invoice_item_uses_product_price_snapshot(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )

    assert item.invoice_id == invoice_john
    assert item.product_id == product_widget.id
    assert item.quantity == 2
    assert item.unit_cost_cents == 1000
    assert item.cost_total_cents == 2000
    assert item.unit_price_cents == 2500
    assert item.line_total_cents == 5000
    assert item.profit_total_cents == 3000


def test_create_invoice_item_can_override_unit_price(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
            unit_price_cents=3000,
        ),
    )

    assert item.unit_price_cents == 3000
    assert item.line_total_cents == 6000


def test_create_invoice_item_can_override_unit_cost(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
            unit_cost_cents=1200,
        ),
    )

    assert item.unit_cost_cents == 1200
    assert item.cost_total_cents == 2400
    assert item.profit_total_cents == 2600


def test_create_invoice_item_recalculates_invoice_total(cursor, invoice_item_repo, invoice_john, product_widget):
    invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )

    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    assert invoice["total"] == 5000


def test_list_by_invoice_id_returns_invoice_items(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
        ),
    )

    results = invoice_item_repo.list_by_invoice_id(invoice_john)

    assert results == [item]


def test_update_invoice_item_recalculates_invoice_total(cursor, invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=1,
        ),
    )

    updated = invoice_item_repo.update(item.id, quantity=3)

    assert updated.quantity == 3
    assert updated.line_total_cents == 7500
    assert invoices.get_invoice_by_id(cursor, invoice_john)["total"] == 7500


def test_update_invoice_item_product_resets_unit_price(
    cursor,
    invoice_item_repo,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )

    updated = invoice_item_repo.update(item.id, product_id=product_service.id)

    assert updated.product_id == product_service.id
    assert updated.unit_cost_cents == 1500
    assert updated.cost_total_cents == 3000
    assert updated.unit_price_cents == 4000
    assert updated.line_total_cents == 8000
    assert updated.profit_total_cents == 5000
    assert invoices.get_invoice_by_id(cursor, invoice_john)["total"] == 8000


def test_update_invoice_item_product_allows_unit_price_override(
    invoice_item_repo,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )

    updated = invoice_item_repo.update(
        item.id,
        product_id=product_service.id,
        unit_price_cents=4500,
    )

    assert updated.product_id == product_service.id
    assert updated.unit_price_cents == 4500
    assert updated.line_total_cents == 9000


def test_update_invoice_item_product_allows_unit_cost_override(
    invoice_item_repo,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )

    updated = invoice_item_repo.update(
        item.id,
        product_id=product_service.id,
        unit_cost_cents=1800,
    )

    assert updated.product_id == product_service.id
    assert updated.unit_cost_cents == 1800
    assert updated.cost_total_cents == 3600
    assert updated.profit_total_cents == 4400


def test_update_invoice_item_rejects_inactive_replacement_product(
    cursor,
    invoice_item_repo,
    invoice_john,
    product_widget,
    product_service,
):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
        ),
    )
    products.update_product(cursor, product_service.id, is_active=False)

    with pytest.raises(ValueError):
        invoice_item_repo.update(item.id, product_id=product_service.id)


def test_delete_invoice_item_recalculates_invoice_total(cursor, invoice_item_repo, invoice_john, product_widget):
    first = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=2,
        ),
    )
    invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
            quantity=1,
        ),
    )

    assert invoice_item_repo.delete(first.id) is True

    assert invoices.get_invoice_by_id(cursor, invoice_john)["total"] == 2500


def test_delete_missing_invoice_item_returns_false(invoice_item_repo):
    assert invoice_item_repo.delete(9999) is False


def test_update_missing_invoice_item_returns_none(invoice_item_repo):
    assert invoice_item_repo.update(9999, quantity=2) is None


def test_create_invoice_item_rejects_missing_invoice(invoice_item_repo, product_widget):
    with pytest.raises(ValueError):
        invoice_item_repo.create(
            invoice_items.InvoiceItemCreate(invoice_id=9999, product_id=product_widget.id),
        )


def test_create_invoice_item_rejects_missing_product(invoice_item_repo, invoice_john):
    with pytest.raises(ValueError):
        invoice_item_repo.create(
            invoice_items.InvoiceItemCreate(invoice_id=invoice_john, product_id=9999),
        )


def test_create_invoice_item_rejects_inactive_product(cursor, invoice_item_repo, invoice_john, product_widget):
    products.update_product(cursor, product_widget.id, is_active=False)

    with pytest.raises(ValueError):
        invoice_item_repo.create(
            invoice_items.InvoiceItemCreate(
                invoice_id=invoice_john,
                product_id=product_widget.id,
            ),
        )


def test_create_invoice_item_rejects_invalid_quantity(invoice_item_repo, invoice_john, product_widget):
    with pytest.raises(ValueError):
        invoice_item_repo.create(
            invoice_items.InvoiceItemCreate(
                invoice_id=invoice_john,
                product_id=product_widget.id,
                quantity=0,
            ),
        )


def test_update_invoice_item_rejects_invalid_unit_price(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
        ),
    )

    with pytest.raises(ValueError):
        invoice_item_repo.update(item.id, unit_price_cents=-1)


def test_update_invoice_item_rejects_invalid_unit_cost(invoice_item_repo, invoice_john, product_widget):
    item = invoice_item_repo.create(
        invoice_items.InvoiceItemCreate(
            invoice_id=invoice_john,
            product_id=product_widget.id,
        ),
    )

    with pytest.raises(ValueError):
        invoice_item_repo.update(item.id, unit_cost_cents=-1)
