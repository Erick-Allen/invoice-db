import pytest
from invoice_db.db import invoices

INVALID_CUSTOMER_ID = 9999
INVALID_INVOICE_ID = 8888
NEGATIVE_TOTAL = -9999

# ---------- Invoice Validation ----------
def test_create_invoice_invalid_customer_raises(cursor):
    with pytest.raises(ValueError):
        invoices.add_invoice_to_customer(cursor, INVALID_CUSTOMER_ID, "1/1/2025", 100.25)

def test_create_invoice_invalid_date_issued_raises(cursor, customer_john):
    with pytest.raises(ValueError):
        invoices.add_invoice_to_customer(cursor, customer_john, "invalid-date", 0)

def test_create_invoice_negative_total_raises(cursor, customer_john):
    with pytest.raises(ValueError):
        invoices.add_invoice_to_customer(cursor, customer_john, "2/18/2025", NEGATIVE_TOTAL)

def test_create_invoice_non_numeric_total_raises(cursor, customer_john):
    with pytest.raises(ValueError):
        invoices.add_invoice_to_customer(cursor, customer_john, "2/18/2025", "Test")

def test_update_invoice_invalid_date_issued_raises(cursor, invoice_john):
    with pytest.raises(ValueError):
        invoices.update_invoice(cursor, invoice_john, date_issued="invalid-date")

def test_update_invoice_invalid_date_due_raises(cursor, invoice_john):
    with pytest.raises(ValueError):
        invoices.update_invoice(cursor, invoice_john, date_due="invalid-date")

def test_update_invoice_negative_total_raises(cursor, invoice_john):
    with pytest.raises(ValueError):
        invoices.update_invoice(cursor, invoice_john, total=NEGATIVE_TOTAL)

def test_update_invoice_invalid_customer_id_raises(cursor, invoice_john):
    with pytest.raises(ValueError):
        invoices.update_invoice(cursor, invoice_john, customer_id=INVALID_CUSTOMER_ID)

def test_delete_invalid_invoice_id_returns_false(cursor):
    assert not invoices.delete_invoice(cursor, INVALID_INVOICE_ID)

def test_get_invoices_by_customer_and_range_invalid_start_raises(cursor, customer_john):
    with pytest.raises(ValueError):
        invoices.get_invoices_by_customer_and_range(cursor, customer_john, "invalid-date", "2/20/2025")

def test_get_invoices_by_customer_and_range_invalid_end_raises(cursor, customer_john):
    with pytest.raises(ValueError):
        invoices.get_invoices_by_customer_and_range(cursor, customer_john, "2/20/2025", "invalid-date")

def test_get_invoices_by_customer_id_empty_list(cursor, customer_john):
    invoice_list = invoices.get_invoices_by_customer_id(cursor, customer_john)
    assert invoice_list == []