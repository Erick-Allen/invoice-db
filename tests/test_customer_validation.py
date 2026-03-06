import pytest
from invoice_db.db import customers

CUSTOMER_JOHN_NAME = "John"
CUSTOMER_JOHN_EMAIL = "john@test.com"
CUSTOMER_ALICE_NAME = "Alice"
CUSTOMER_ALICE_EMAIL = "alice@test.com"

# ---------- Customer Validation ----------
def test_create_customer_empty_name_raises(cursor):
    with pytest.raises(ValueError):
        customers.create_customer(cursor, " ", "john@example.com")

def test_create_customer_invalid_name_raises(cursor):
    with pytest.raises(ValueError):
        customers.create_customer(cursor, "John 2 Doe", "johndoe@example.com")

def test_create_customer_empty_email_raises(cursor):
    with pytest.raises(ValueError):
        customers.create_customer(cursor, "John Doe", " ")

def test_create_customer_invalid_email_raises(cursor):
    with pytest.raises(ValueError):
        customers.create_customer(cursor, "John Doe", "invalid-email")

def test_create_customer_duplicate_name_allowed(cursor):
    customer1_id = customers.create_customer(cursor, "John", "first@test.com")
    customer2_id = customers.create_customer(cursor, "John", "second@test.com")
    assert customer1_id != customer2_id

def test_create_customer_duplicate_email_raises(cursor):
    customers.create_customer(cursor, "John Doe", "same@example.com")
    with pytest.raises(ValueError):
        customers.create_customer(cursor, "John Doe", "same@example.com")

def test_update_customer_duplicate_email_raises(cursor, customer_john, customer_alice):
    with pytest.raises(ValueError):
        customers.update_customer(cursor, customer_alice, email=CUSTOMER_JOHN_EMAIL)

def test_delete_customer_invalid_id_returns_false(cursor):
    assert not customers.delete_customer(cursor, -9999)