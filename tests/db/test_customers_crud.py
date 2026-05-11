from invoice_db.db import customers, invoices

CUSTOMER_JOHN_NAME = "John"
CUSTOMER_JOHN_EMAIL = "john@test.com"
CUSTOMER_ALICE_NAME = "Alice"
CUSTOMER_ALICE_EMAIL = "alice@test.com"

# ---------- Customer CRUD Tests ----------
def test_create_customer(cursor):
    name, email = "Tom", "tom@test.com"
    customer_id = customers.create_customer(cursor, name, email)
    row = cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    assert row is not None
    assert row['name'] == name
    assert row['email'] == email


def test_get_customer_by_id(cursor, customer_john):
    row = customers.get_customer_by_id(cursor, customer_john)
    assert row['id'] == customer_john

def test_get_customer_by_email(cursor, customer_john):
    row = customers.get_customer_by_email(cursor, "john@test.com")
    assert row is not None
    assert row['name'] == CUSTOMER_JOHN_NAME
    assert row['email'] == CUSTOMER_JOHN_EMAIL

def test_get_customer_id_by_email(cursor, customer_john):
    got_id = customers.get_customer_id_by_email(cursor, "john@test.com")
    assert got_id == customer_john

def test_get_customer(cursor, customer_john, customer_alice):
    rows = customers.get_customers(cursor)

    assert len(rows) == 2

    customer_1 = next((u for u in rows if u['id'] == customer_john), None)
    customer_2 = next((u for u in rows if u['id'] == customer_alice), None)

    assert customer_1 is not None
    assert customer_2 is not None
    assert customer_1['name'] == CUSTOMER_JOHN_NAME
    assert customer_1['email'] == CUSTOMER_JOHN_EMAIL
    assert customer_2['name'] == CUSTOMER_ALICE_NAME
    assert customer_2['email'] == CUSTOMER_ALICE_EMAIL

def test_get_customer_filter_by_min_total(cursor):
    customer_id_1 = customers.create_customer(cursor, CUSTOMER_JOHN_NAME, CUSTOMER_JOHN_EMAIL)
    customer_id_2 = customers.create_customer(cursor, CUSTOMER_ALICE_NAME, CUSTOMER_ALICE_EMAIL)
    invoice_id_1 = invoices.add_invoice_to_customer(cursor, customer_id_1, "1/1/2025", 200)
    invoice_id_2 = invoices.add_invoice_to_customer(cursor, customer_id_1, "1/1/2025", 300)

    rows = customers.get_customers(cursor, min_total_dollars=500)
    assert len(rows) == 1

    returned_ids = {r["id"] for r in rows}
    assert customer_id_1 in returned_ids
    assert customer_id_2 not in returned_ids

def test_update_customer_name_only(cursor, customer_john):
    updated_name = "Timmy"
    customer_was_updated = customers.update_customer(cursor, customer_john, name=updated_name)
    updated_customer = customers.get_customer_by_id(cursor, customer_john)

    assert customer_was_updated
    assert updated_customer['name'] == updated_name
    assert updated_customer['email'] == CUSTOMER_JOHN_EMAIL

def test_update_customer_email_only(cursor, customer_john):
    updated_email = "paul@gmail.com"
    customer_was_updated = customers.update_customer(cursor, customer_john, email=updated_email)
    updated_customer = customers.get_customer_by_id(cursor, customer_john)
    
    assert customer_was_updated
    assert updated_customer['name'] == CUSTOMER_JOHN_NAME
    assert updated_customer['email'] == updated_email

def test_update_customer_name_and_email(cursor, customer_john):
    updated_name = "Melissa"
    updated_email = "melissa@test.com"
    customer_was_updated = customers.update_customer(cursor, customer_john, name=updated_name, email=updated_email)
    updated_customer = customers.get_customer_by_id(cursor, customer_john)

    assert customer_was_updated
    assert updated_customer['name'] == updated_name
    assert updated_customer['email'] == updated_email

def test_update_customer_no_fields_returns_false(cursor, customer_john):
    assert not customers.update_customer(cursor, customer_john)

def test_delete_customer(cursor, customer_john):
    customer_was_deleted = customers.delete_customer(cursor, customer_john)
    row = customers.get_customer_by_id(cursor, customer_john)
    
    assert customer_was_deleted
    assert row is None