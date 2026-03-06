from invoice_db.db import customers, invoices, utils

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

def test_get_invoice_by_id(cursor, customer_john):
    invoice_id = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    row = invoices.get_invoice_by_id(cursor, invoice_id)

    assert row['id'] == invoice_id

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

def test_count_invoices(cursor, customer_john):
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_john, "1/20/2025", 300.25)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_john, "2/17/2025", 100)
    invoice_id_3 = invoices.add_invoice_to_customer(cursor, customer_john, "6/5/2025", 1000.01)

    invoice_count = invoices.count_invoices(cursor)

    assert invoice_count == 3

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