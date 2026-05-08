import sqlite3
from invoice_db.db import customers as customers_db
from invoice_db.db import invoices as invoices_db
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

def _normalize_invoice_status(status: str | None) -> str | None:
    if status is None:
        return None
    
    status = status.strip().lower()
    
    if status == "":
        return None
    
    if status not in VALID_INVOICE_STATUSES:
        raise exceptions.ValidationError("Invoice status must be one of: draft, sent, paid, void.")
    
    return status
    
def _validate_positive_id(value: int | None, label: str) -> None:
    if value is None:
        return
    if value <= 0:
        raise exceptions.ValidationError(f"{label} must be a positive integer.")
    
def _validate_total(total: float) -> None:
    if total <= 0:
        raise exceptions.ValidationError("Invoice total must be greater than 0.")
    
def _validate_total_range(min_total: float | None = None, max_total: float | None = None) -> None:
    if min_total is not None and min_total < 0:
        raise exceptions.ValidationError("Minimum total cannot be negative.")

    if max_total is not None and max_total < 0:
        raise exceptions.ValidationError("Maximum total cannot be negative.")
    
    if min_total is not None and max_total is not None and min_total > max_total:
        raise exceptions.ValidationError("Minimum total cannot be greater than maximum total.")

def _validate_pagination(limit: int, offset: int) -> None:
    if limit <= 0:
        raise exceptions.ValidationError("Limit must be greater than 0.")
    
    if offset < 0:
        raise exceptions.ValidationError("Offset cannot be negative.")
    
def _normalize_sort_by(sort_by: str, allowed_fields: set[str]) -> str:
    sort_by = sort_by.strip().lower()

    if sort_by == "":
        raise exceptions.ValidationError("Sort field cannot be empty.")
    
    if sort_by not in allowed_fields:
        allowed = ", ".join(sorted(allowed_fields))
        raise exceptions.ValidationError(f"Sort field must be one of: {allowed}.")
    
    return sort_by

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
    _validate_positive_id(customer_id, "Customer id")
        
    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")

    return customer

def _require_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    _validate_positive_id(invoice_id, "Invoice id")
        
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")

    return invoice

def _prepare_invoice_changes(
    cursor,
    invoice: sqlite3.Row,
    new_date_issued: str | None = None,
    new_date_due: str | None = None,
    new_total: float | None = None,
    new_customer_id: int | None = None,
) -> tuple[str | None, str | None, float | None, int | None]:
    if (
        new_date_issued is None
        and new_date_due is None
        and new_total is None
        and new_customer_id is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the invoice.")
    
    normalized_date_issued = None if new_date_issued is None else _normalize_invoice_date(new_date_issued, "Date issued")
    normalized_date_due = None if new_date_due is None else _normalize_invoice_date(new_date_due, "Date due")
   
    if new_total is not None:
        _validate_total(new_total)

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
        and (new_total is None or new_total == invoice['total'])
        and (normalized_customer is None or normalized_customer == invoice['customer_id'])
    ):
        raise exceptions.ValidationError("No changes detected.")
    
    return normalized_date_issued, normalized_date_due, new_total, normalized_customer

def _update_invoice(
    cursor,
    invoice: sqlite3.Row,
    new_date_issued: str | None = None,
    new_date_due: str | None = None,
    new_total: float | None = None,
    new_customer_id: int | None = None,
) -> sqlite3.Row:
    date_issued, date_due, total, customer_id = _prepare_invoice_changes(
        cursor,
        invoice=invoice,
        new_date_issued=new_date_issued,
        new_date_due=new_date_due,
        new_total=new_total,
        new_customer_id=new_customer_id,
    )

    try:
        updated = invoices_db.update_invoice(
            cursor=cursor,
            invoice_id=invoice['id'],
            date_issued=date_issued,
            date_due=date_due,
            total=total,
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

#CRUD 
def create_invoice(
    cursor, 
    customer_id: int, 
    total: float, 
    date_issued: str | None, 
    date_due: str | None,
) -> InvoiceRecord:
    _require_customer(cursor, customer_id)
    _validate_total(total)
    date_issued, date_due = _prepare_invoice_dates(date_issued, date_due)
    
    try:
        invoice_id = invoices_db.add_invoice_to_customer(
            cursor,
            customer_id=customer_id,
            total=total,
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
    _validate_positive_id(customer_id, "Customer id")    
    _validate_total_range(min_total, max_total)
    _validate_pagination(limit, offset)
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
    _validate_total_range(min_total, max_total)

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

    _validate_total_range(min_total, max_total)
    _validate_pagination(limit, offset)
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
    invoice = _require_invoice(cursor, invoice_id)

    updated_invoice = _update_invoice(
        cursor,
        invoice=invoice,
        new_date_issued=new_date_issued,
        new_date_due=new_date_due,
        new_total=new_total,
        new_customer_id=new_customer_id
    )

    return _to_invoice_record(updated_invoice)
    
def set_invoice_status(cursor, invoice_id: int, status: str) -> InvoiceRecord:
    invoice = _require_invoice(cursor, invoice_id)
    normalized_status = _normalize_invoice_status(status)

    if normalized_status == invoice['status']:
        raise exceptions.ValidationError("No status change detected.")
    
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
    _validate_positive_id(invoice_id, "Invoice id")
    deleted_invoice = invoices_db.delete_invoice(cursor, invoice_id)

    if not deleted_invoice:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")