import sqlite3
from typing import TypedDict

from invoice_db.db import invoice_items as invoice_items_db
from invoice_db.db import invoices as invoices_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


LOCKED_INVOICE_STATUSES = {"sent", "paid", "void"}


class InvoiceItemRecord(TypedDict):
    id: int
    invoice_id: int
    product_id: int
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    created_at: str
    updated_at: str


def _to_invoice_item_record(item: invoice_items_db.InvoiceItem) -> InvoiceItemRecord:
    return {
        "id": item.id,
        "invoice_id": item.invoice_id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "unit_price_cents": item.unit_price_cents,
        "line_total_cents": item.line_total_cents,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _validate_id(value: int, label: str) -> None:
    try:
        validate_positive_id(value, label)
    except ValueError as e:
        raise _as_validation_error(e) from e


def _require_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    _validate_id(invoice_id, "Invoice id")
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")
    return invoice


def _require_editable_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    invoice = _require_invoice(cursor, invoice_id)
    if invoice["status"] in LOCKED_INVOICE_STATUSES:
        raise exceptions.ConflictError(
            "Invoice line items cannot be changed after an invoice is sent, paid, or void."
        )
    return invoice


def _require_invoice_item(
    repository: invoice_items_db.InvoiceItemRepository,
    invoice_item_id: int,
) -> invoice_items_db.InvoiceItem:
    _validate_id(invoice_item_id, "Invoice item id")
    item = repository.get_by_id(invoice_item_id)
    if item is None:
        raise exceptions.NotFoundError(f"Invoice item not found (id={invoice_item_id})")
    return item


def create_invoice_item(
    cursor,
    invoice_id: int,
    product_id: int,
    quantity: int = 1,
    unit_price_cents: int | None = None,
) -> InvoiceItemRecord:
    _require_editable_invoice(cursor, invoice_id)
    _validate_id(product_id, "Product id")
    repository = invoice_items_db.InvoiceItemRepository(cursor)

    try:
        item = repository.create(
            invoice_items_db.InvoiceItemCreate(
                invoice_id=invoice_id,
                product_id=product_id,
                quantity=quantity,
                unit_price_cents=unit_price_cents,
            )
        )
    except ValueError as e:
        message = str(e)
        if message.startswith("Product not found"):
            raise exceptions.NotFoundError(message) from e
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid invoice item data.") from e

    return _to_invoice_item_record(item)


def list_invoice_items(cursor, invoice_id: int) -> list[InvoiceItemRecord]:
    _require_invoice(cursor, invoice_id)
    repository = invoice_items_db.InvoiceItemRepository(cursor)
    return [
        _to_invoice_item_record(item)
        for item in repository.list_by_invoice_id(invoice_id)
    ]


def get_invoice_item_by_id(cursor, invoice_item_id: int) -> InvoiceItemRecord:
    repository = invoice_items_db.InvoiceItemRepository(cursor)
    return _to_invoice_item_record(_require_invoice_item(repository, invoice_item_id))


def update_invoice_item_by_id(
    cursor,
    invoice_item_id: int,
    *,
    product_id: int | None = None,
    quantity: int | None = None,
    unit_price_cents: int | None = None,
) -> InvoiceItemRecord:
    if product_id is None and quantity is None and unit_price_cents is None:
        raise exceptions.ValidationError("Please provide at least one value to update the invoice item.")

    if product_id is not None:
        _validate_id(product_id, "Product id")

    repository = invoice_items_db.InvoiceItemRepository(cursor)
    item = _require_invoice_item(repository, invoice_item_id)
    _require_editable_invoice(cursor, item.invoice_id)

    try:
        updated_item = repository.update(
            invoice_item_id,
            product_id=product_id,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
        )
    except ValueError as e:
        message = str(e)
        if message.startswith("Product not found"):
            raise exceptions.NotFoundError(message) from e
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid invoice item update data.") from e

    if updated_item is None:
        raise exceptions.ServiceError(f"Failed to update invoice item {invoice_item_id}.")

    return _to_invoice_item_record(updated_item)


def delete_invoice_item(cursor, invoice_item_id: int) -> None:
    repository = invoice_items_db.InvoiceItemRepository(cursor)
    item = _require_invoice_item(repository, invoice_item_id)
    _require_editable_invoice(cursor, item.invoice_id)

    deleted = repository.delete(invoice_item_id)
    if not deleted:
        raise exceptions.NotFoundError(f"Invoice item not found (id={invoice_item_id})")
