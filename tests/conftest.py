import sqlite3
import pytest
from invoice_db.db import schema, customers, invoices
from datetime import date, timedelta

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
        cursor=cursor, 
        customer_id=customer_john,
        date_issued=date.today().isoformat(),
        total=1234.00,
        status="draft",
        )

@pytest.fixture
def invoice_alice(cursor, customer_alice):
    return invoices.add_invoice_to_customer(
        cursor=cursor, 
        customer_id=customer_alice,
        date_issued=date.today().isoformat(),
        total=100.25,
        status="draft",
        )

@pytest.fixture
def invoice_query_data(cursor, customer_john, customer_alice):
    today = date.today().isoformat()
    future = (date.today() + timedelta(days=30)).isoformat()

    invoice_john_draft = invoices.add_invoice_to_customer(
            cursor, 
            customer_id=customer_john, 
            total=100.00, 
            date_issued=today,
            date_due=future, 
            status="draft",
    )

    invoice_john_sent = invoices.add_invoice_to_customer(
            cursor, 
            customer_id=customer_john, 
            total=250.00, 
            date_issued=today,
            date_due=future,
            status="draft",
    )


    invoice_alice_paid = invoices.add_invoice_to_customer(
            cursor, 
            customer_id=customer_alice, 
            total=500.00, 
            date_issued=today,
            date_due=future,
            status="draft",
    )

    invoice_alice_void = invoices.add_invoice_to_customer(
            cursor,
            customer_id=customer_alice,
            total=175.00, 
            date_issued=today,
            date_due=future,
            status="draft",
    )

    status_updates = [
        (invoice_john_sent, "sent"),
        (invoice_alice_paid, "paid"),
        (invoice_alice_void, "void")
    ]

    for invoice_id, status in status_updates:
        cursor.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (status, invoice_id),
        )

    return {
        "customers": {
            "john": customer_john,
            "alice": customer_alice,
        },
        "invoices": {
            "john_draft": invoice_john_draft,
            "john_sent": invoice_john_sent,
            "alice_paid": invoice_alice_paid,
            "alice_void": invoice_alice_void,
        }
    }

@pytest.fixture
def invoice_overdue_data(cursor, customer_john, customer_alice):
    today = date.today()
    issued_date = (today - timedelta(days=30)).isoformat()

    past_due = (today - timedelta(days=10)).isoformat()
    due_today = today.isoformat()
    future_due = (today + timedelta(days=10)).isoformat()

    john_overdue = invoices.add_invoice_to_customer(
        cursor,
        customer_id=customer_john,
        total=300,
        date_issued=issued_date,
        date_due=past_due,
        status="draft",
    )

    john_due_today = invoices.add_invoice_to_customer(
        cursor,
        customer_id=customer_john,
        total=200,
        date_issued=issued_date,
        date_due=due_today,
        status="draft",
    )

    alice_overdue = invoices.add_invoice_to_customer(
        cursor,
        customer_id=customer_alice,
        total=500,
        date_issued=issued_date,
        date_due=past_due,
        status="draft",
    )

    alice_not_overdue = invoices.add_invoice_to_customer(
        cursor,
        customer_id=customer_alice,
        total=400,
        date_issued=issued_date,
        date_due=future_due,
        status="draft",
    )

    cursor.execute(
        "UPDATE invoices SET status = 'sent' WHERE id IN (?,?,?,?)",
        (john_overdue, john_due_today, alice_overdue, alice_not_overdue),    
    )

    return {""
        "customers":{
            "john": customer_john,
            "alice": customer_alice,
        },
        "invoices": {
            "john_overdue": john_overdue,
            "john_due_today": john_due_today,
            "alice_overdue": alice_overdue,
            "alice_not_overdue": alice_not_overdue,
        }
    }