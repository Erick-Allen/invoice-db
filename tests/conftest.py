import sqlite3
import pytest
from invoice_db.db import schema, customers, invoices

# DB fixtures
@pytest.fixture
def db():
    connect = sqlite3.connect(":memory:")
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    schema.create_customer_schema(cursor)
    schema.create_invoice_schema(cursor)
    connect.commit()

    yield connect

    connect.close()

@pytest.fixture
def cursor(db):
    return db.cursor()

@pytest.fixture
def customer_john(cursor):
    return customers.create_customer(cursor, "John", "john@test.com")

@pytest.fixture
def customer_alice(cursor):
    return customers.create_customer(cursor, "Alice", "alice@test.com")

@pytest.fixture
def invoice_john(cursor, customer_john):
    return invoices.add_invoice_to_customer(
        cursor, 
        customer_john,
        "2/18/2025",
        1234
        )