from datetime import date, timedelta
from invoice_db.db import customers, invoices, utils
import pytest

CUSTOMER_JOHN_EMAIL = "john@test.com"

# ---------- Invoice CRUD Tests ----------
def test_create_invoice(cursor, customer_john):
    invoice_id = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    row = cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()

    assert row is not None
    assert row['id'] == invoice_id
    assert row['customer_id'] == customer_john
    assert row['date_issued'] == "2025-01-20"
    assert row['total'] == 30025
    assert row["date_due"] is None

def test_get_invoice_by_id(cursor, invoice_john):
    row = invoices.get_invoice_by_id(cursor, invoice_john)
    assert row['id'] == invoice_john

def test_get_invoices_by_email(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)
    rows = invoices.get_invoices_by_email(cursor, CUSTOMER_JOHN_EMAIL)

    assert len(rows) == 2

    invoice_1 = next((i for i in rows if i['id'] == invoice_id_1), None)
    invoice_2 = next((i for i in rows if i['id'] == invoice_id_2), None)
    
    assert invoice_1 is not None
    assert invoice_2 is not None
    assert invoice_1["customer_id"] == customer_john
    assert invoice_2["customer_id"] == customer_john
    assert invoice_1["id"] == invoice_id_1
    assert invoice_2["id"] == invoice_id_2

def test_get_invoices_by_customer_id(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)
    rows = invoices.get_invoices_by_customer_id(cursor, customer_john)

    assert len(rows) == 2

    customer_ids = {r["customer_id"] for r in rows}
    assert customer_ids == {customer_john}

def test_get_invoices_by_customer_and_range_inclusive(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)
    invoice_id_3 = invoices.add_invoice_to_customer(cursor, customer_john, "6/5/2025", 1000.01)

    start_date = "2/17/2025"
    end_date = "6/5/2025"
    rows = invoices.get_invoices_by_customer_and_range(cursor, customer_john, start_date, end_date)

    assert len(rows) == 2

    invoice_1 = next((i for i in rows if i['id'] == invoice_id_1), None)
    invoice_2 = next((i for i in rows if i['id'] == invoice_id_2), None)
    invoice_3 = next((i for i in rows if i['id'] == invoice_id_3), None)

    
    assert invoice_1 is None
    assert invoice_2 is not None
    assert invoice_3 is not None
    assert invoice_2["customer_id"] == customer_john
    assert invoice_3["customer_id"] == customer_john
    assert invoice_2["id"] == invoice_id_2
    assert invoice_3["id"] == invoice_id_3

@pytest.mark.parametrize("new_status", ["draft", "sent", "paid", "void"])
def test_same_status_update_returns_success(cursor, new_status, customer_john):
    invoice_id = invoices.add_invoice_to_customer(
        cursor,
        customer_id=customer_john,
        total=100.5,
        status="draft",
    )

    if new_status != "draft":
        invoices.set_invoice_status(cursor, invoice_id=invoice_id, status="sent")
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_id, status=new_status)
    invoice = invoices.get_invoice_by_id(cursor, invoice_id)
    assert result is True
    assert invoice['status'] == new_status

def test_valid_transition_draft_to_sent_autofills_date_issued_and_date_due(cursor, customer_john):
    invoice_id = invoices.add_invoice_to_customer(cursor, customer_id=customer_john, total=100)
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_id, status="sent")
    updated_invoice = invoices.get_invoice_by_id(cursor, invoice_id=invoice_id)
    assert result is True
    assert updated_invoice['status'] == "sent"
    assert updated_invoice['date_issued'] == date.today().isoformat()
    assert updated_invoice['date_due'] == (date.today() + timedelta(days=30)).isoformat()

def test_draft_to_sent_keeps_valid_existing_dates(cursor, customer_john):
    invoice_id = invoices.add_invoice_to_customer(cursor, customer_id=customer_john, total=100, date_issued="01/01/2100", date_due="02/01/2100")
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_id, status="sent")
    invoice = invoices.get_invoice_by_id(cursor, invoice_id)
    assert result is True
    assert invoice['status'] == "sent"
    assert invoice['date_issued'] == "2100-01-01"
    assert invoice['date_due'] == "2100-02-01"


def test_valid_transistion_sent_to_paid(cursor, invoice_john):
    invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="sent")
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="paid")
    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    assert result is True
    assert invoice['status'] == "paid"

def test_valid_transistion_sent_to_void(cursor, invoice_john):
    invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="sent")
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="void")
    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    assert result is True
    assert invoice['status'] == "void"

def test_valid_transistion_paid_to_sent(cursor, invoice_john):
    invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="sent")
    invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="paid")
    result = invoices.set_invoice_status(cursor, invoice_id=invoice_john, status="sent")
    invoice = invoices.get_invoice_by_id(cursor, invoice_john)
    assert result is True
    assert invoice['status'] == "sent"

def test_update_invoice_date_issued_only(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)

    new_date_issued = "2025-03-08"
    updated = invoices.update_invoice(cursor, invoice_id_1, date_issued=new_date_issued)
    assert updated

    row_1 = invoices.get_invoice_by_id(cursor, invoice_id_1)
    row_2 = invoices.get_invoice_by_id(cursor, invoice_id_2)

    assert row_1["date_issued"] == new_date_issued
    assert row_2["date_issued"] != new_date_issued

def test_update_invoice_total_and_customer(cursor, customer_john, customer_alice):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)

    new_total = 1500.90
    updated = invoices.update_invoice(cursor, invoice_id_2, total=new_total, customer_id=customer_alice)
    assert updated

    row_1 = invoices.get_invoice_by_id(cursor, invoice_id_1)
    row_2 = invoices.get_invoice_by_id(cursor, invoice_id_2)

    assert row_1["customer_id"] == customer_john
    assert row_1["total"] != utils.to_cents(new_total)
    assert row_2["customer_id"] == customer_alice
    assert row_2["total"] == utils.to_cents(new_total)
    

def test_update_invoice_no_fields_returns_false(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)

    updated = invoices.update_invoice(cursor, invoice_id_1)
    assert not updated

def test_delete_invoice(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)

    deleted = invoices.delete_invoice(cursor, invoice_id_1)
    assert deleted

    remaining = invoices.get_invoices_by_customer_id(cursor, customer_john)
    remaining_ids = {r["id"] for r in remaining}
    assert invoice_id_1 not in remaining_ids
    assert invoice_id_2 in remaining_ids

def test_delete_customer_cascades_invoices(cursor, customer_john, invoice_john):
    deleted_customer = customers.delete_customer(cursor, customer_john)
    assert deleted_customer

    cascaded_invoices = invoices.get_invoices_by_customer_id(cursor, customer_john)
    assert cascaded_invoices == []

    row = customers.get_customer_by_id(cursor, customer_john)
    assert row is None