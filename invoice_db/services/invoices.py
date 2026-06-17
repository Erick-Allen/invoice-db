import sqlite3
from invoice_db.db import customers as customers_db
from invoice_db.db import invoice_items as invoice_items_db
from invoice_db.db import invoices as invoices_db
from invoice_db.db import products as products_db
from invoice_db.db.validators import (
    normalize_sort_by,
    normalize_status,
    validate_pagination,
    validate_positive_id,
    validate_total_range,
)
from invoice_db.utils import to_iso
from typing import TypedDict
from . import exceptions

VALID_INVOICE_STATUSES = {"draft", "sent", "paid", "void"}
VALID_INVOICE_SORT_FIELDS = {"id", "created_at", "date_issued", "date_due", "total", "status"}
VALID_OVERDUE_SORT_FIELDS = {"id", "date_issued", "date_due", "total", "days_overdue"}

class InvoiceRecord(TypedDict):
    id: int
    customer_id: int
    total: float
    status: str
    date_issued: str | None
    date_due: str | None

class InvoiceCountResult(TypedDict):
    count: int
    customer: dict | None
    status: str | None
    min_total: float | None
    max_total: float | None

class OverdueInvoiceRecord(TypedDict):
    id: int
    customer_id: int
    total: float
    status: str
    date_issued: str | None
    date_due: str | None
    days_overdue: int

def _to_invoice_record(row: sqlite3.Row) -> InvoiceRecord:
    return dict(row)

def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))

def _normalize_invoice_status(status: str | None) -> str | None:
    try:
        return normalize_status(status, VALID_INVOICE_STATUSES)
    except ValueError as e:
        raise _as_validation_error(e) from e
    
def _normalize_sort_by(sort_by: str, allowed_fields: set[str]) -> str:
    try:
        return normalize_sort_by(sort_by, allowed_fields)
    except ValueError as e:
        raise _as_validation_error(e) from e

def _normalize_invoice_date(date_value: str | None, label: str) -> str | None:
    try:
        return to_iso(date_value)
    except ValueError as e:
        raise exceptions.ValidationError(f"{label}: {e}") from e
    
def _prepare_invoice_dates(
    date_issued: str | None = None,
    date_due: str | None = None,
) -> tuple[str | None, str | None]:
    normalized_issued = _normalize_invoice_date(date_issued, "Date issued")
    normalized_due = _normalize_invoice_date(date_due, "Date due")

    if normalized_issued is not None and normalized_due is not None:
        if normalized_due < normalized_issued:
            raise exceptions.ValidationError("Date due cannot be before date issued.")
        
    return normalized_issued, normalized_due
    
def _require_customer(cursor, customer_id: int) -> sqlite3.Row:
    try:
        validate_positive_id(customer_id, "Customer id")
    except ValueError as e:
        raise _as_validation_error(e) from e
        
    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")

    return customer

def _require_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    try:
        validate_positive_id(invoice_id, "Invoice id")
    except ValueError as e:
        raise _as_validation_error(e) from e
        
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")

    return invoice

def _prepare_invoice_changes(
    cursor,
    invoice: sqlite3.Row,
    new_date_issued: str | None = None,
    new_date_due: str | None = None,
    new_customer_id: int | None = None,
) -> tuple[str | None, str | None, int | None]:
    if (
        new_date_issued is None
        and new_date_due is None
        and new_customer_id is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the invoice.")
    
    normalized_date_issued = None if new_date_issued is None else _normalize_invoice_date(new_date_issued, "Date issued")
    normalized_date_due = None if new_date_due is None else _normalize_invoice_date(new_date_due, "Date due")
   
    normalized_customer = None
    if new_customer_id is not None:
        _require_customer(cursor, new_customer_id)
        normalized_customer = new_customer_id
        
    effective_date_issued = invoice['date_issued'] if normalized_date_issued is None else normalized_date_issued
    effective_date_due = invoice['date_due'] if normalized_date_due is None else normalized_date_due

    if effective_date_issued is not None and effective_date_due is not None:
        if effective_date_due < effective_date_issued:
            raise exceptions.ValidationError("Date due cannot be before date issued.")
        
    if (
        (normalized_date_issued is None or normalized_date_issued == invoice['date_issued'])
        and (normalized_date_due is None or normalized_date_due == invoice['date_due'])
        and (normalized_customer is None or normalized_customer == invoice['customer_id'])
    ):
        raise exceptions.ValidationError("No changes detected.")
    
    return normalized_date_issued, normalized_date_due, normalized_customer

def _update_invoice(
    cursor,
    invoice: sqlite3.Row,
    new_date_issued: str | None = None,
    new_date_due: str | None = None,
    new_customer_id: int | None = None,
) -> sqlite3.Row:
    date_issued, date_due, customer_id = _prepare_invoice_changes(
        cursor,
        invoice=invoice,
        new_date_issued=new_date_issued,
        new_date_due=new_date_due,
        new_customer_id=new_customer_id,
    )

    try:
        updated = invoices_db.update_invoice(
            cursor=cursor,
            invoice_id=invoice['id'],
            date_issued=date_issued,
            date_due=date_due,
            customer_id=customer_id,
        )
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid invoice update data.") from e
    
    if not updated:
        raise exceptions.ServiceError(f"Failed to update invoice {invoice['id']}")
    
    updated_invoice = invoices_db.get_invoice_by_id(cursor, invoice['id'])
    if updated_invoice is None:
        raise exceptions.ServiceError("Updated invoice, but failed ot reload record.")
    
    return updated_invoice

def _inactive_product_names_for_invoice(cursor, invoice_id: int) -> list[str]:
    repo = invoice_items_db.InvoiceItemRepository(cursor)
    inactive_names = []

    for item in repo.list_by_invoice_id(invoice_id):
        product = products_db.get_product_by_id(cursor, item.product_id)
        if product is not None and not product.is_active:
            inactive_names.append(product.name)

    return inactive_names

#CRUD 
def create_invoice(
    cursor, 
    customer_id: int, 
    date_issued: str | None, 
    date_due: str | None,
    total: float | None = None,
) -> InvoiceRecord:
    _require_customer(cursor, customer_id)
    if total not in (None, 0):
        raise exceptions.ValidationError("Invoice totals are calculated from line items.")
    date_issued, date_due = _prepare_invoice_dates(date_issued, date_due)
    
    try:
        invoice_id = invoices_db.add_invoice_to_customer(
            cursor,
            customer_id=customer_id,
            total=0,
            date_issued=date_issued,
            date_due=date_due,
        )
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid invoice data.") from e
    
    if invoice_id is None:
        raise exceptions.ServiceError("Failed to create invoice.")
    
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.ServiceError("Invoice was created but could not be retrieved.")
    
    return _to_invoice_record(invoice)

def list_invoices(
        cursor,
        customer_id: int | None = None,
        status: str | None = None,
        min_total: float | None = None,
        max_total: float | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        desc: bool = True,
) -> list[InvoiceRecord]:
    try:
        validate_positive_id(customer_id, "Customer id")
        validate_total_range(min_total, max_total)
        validate_pagination(limit, offset)
    except ValueError as e:
        raise _as_validation_error(e) from e
    sort_by = _normalize_sort_by(sort_by, VALID_INVOICE_SORT_FIELDS)    
    status = _normalize_invoice_status(status)

    invoices = invoices_db.list_invoices(
                cursor,
                customer_id=customer_id,
                status=status,
                min_total=min_total,
                max_total=max_total,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )

    return [_to_invoice_record(invoice) for invoice in invoices]

def get_invoice_by_id(cursor, invoice_id: int) -> InvoiceRecord:
    invoice = _require_invoice(cursor, invoice_id)
    return _to_invoice_record(invoice)

def count_invoices(
    cursor,
    customer_id: int | None = None,
    status: str | None = None,
    min_total: float | None = None,
    max_total: float | None = None,
) -> InvoiceCountResult:
    customer = None
    if customer_id is not None:
       customer_row = _require_customer(cursor, customer_id)
       customer = dict(customer_row)
    
    status = _normalize_invoice_status(status)
    try:
        validate_total_range(min_total, max_total)
    except ValueError as e:
        raise _as_validation_error(e) from e

    count = invoices_db.count_invoices(
        cursor,
        customer_id=customer_id,
        status=status,
        min_total=min_total,
        max_total=max_total,
    )

    return {
        "count": count,
        "customer": customer,
        "status": status,
        "min_total": min_total,
        "max_total": max_total,
    }

def overdue_invoices(
    cursor,
    customer_id: int | None = None,
    days_overdue: int | None = None,
    min_total: float | None = None,
    max_total: float | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "date_issued",
    desc: bool = True, 
) -> list[OverdueInvoiceRecord]:
    if customer_id is not None:
        _require_customer(cursor, customer_id)
    
    if days_overdue is not None:
        if days_overdue <= 0:
            raise exceptions.ValidationError("Days overdue must be a positive number.")

    try:
        validate_total_range(min_total, max_total)
        validate_pagination(limit, offset)
    except ValueError as e:
        raise _as_validation_error(e) from e
    sort_by = _normalize_sort_by(sort_by, VALID_OVERDUE_SORT_FIELDS)

    invoices = invoices_db.list_overdue_invoices(
                cursor=cursor,
                customer_id=customer_id,
                days_overdue=days_overdue,
                min_total=min_total,
                max_total=max_total,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )
    
    return [dict(invoice) for invoice in invoices]

def update_invoice_by_id(
    cursor,
    invoice_id: int,
    new_date_issued: str | None = None,
    new_date_due: str | None = None,
    new_total: float | None = None,
    new_customer_id: int | None = None,
    ) -> InvoiceRecord:
    if new_total is not None:
        raise exceptions.ValidationError("Invoice totals are calculated from line items.")

    invoice = _require_invoice(cursor, invoice_id)

    updated_invoice = _update_invoice(
        cursor,
        invoice=invoice,
        new_date_issued=new_date_issued,
        new_date_due=new_date_due,
        new_customer_id=new_customer_id
    )

    return _to_invoice_record(updated_invoice)
    
def set_invoice_status(cursor, invoice_id: int, new_status: str) -> InvoiceRecord:
    invoice = _require_invoice(cursor, invoice_id)
    normalized_status = _normalize_invoice_status(new_status)

    if normalized_status == invoice['status']:
        raise exceptions.ValidationError("No status change detected.")
    
    if invoice["status"] == "draft" and normalized_status == "sent":
        inactive_product_names = _inactive_product_names_for_invoice(cursor, invoice_id)
        if inactive_product_names:
            names = ", ".join(inactive_product_names)
            raise exceptions.ValidationError(
                f"Cannot send invoice with inactive products: {names}."
            )
    
    try:
        updated = invoices_db.set_invoice_status(
            cursor,
            invoice_id=invoice_id,
            status=normalized_status,
        )
    except ValueError as e:
        raise exceptions.ValidationError(str(e)) from e
    
    if not updated:
        raise exceptions.ServiceError(f"Failed to update invoice {invoice_id} status.")
    
    updated_invoice = invoices_db.get_invoice_by_id(cursor, invoice_id=invoice_id)
    if updated_invoice is None:
        raise exceptions.ServiceError("Updated invoice, but failed to reload record.")

    return _to_invoice_record(updated_invoice)

def delete_invoice(cursor, invoice_id: int) -> None:
    try:
        validate_positive_id(invoice_id, "Invoice id")
    except ValueError as e:
        raise _as_validation_error(e) from e
    deleted_invoice = invoices_db.delete_invoice(cursor, invoice_id)

    if not deleted_invoice:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")
