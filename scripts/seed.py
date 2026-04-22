import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from invoice_db.db import schema, customers, invoices, utils

def parse_args():
    parser = argparse.ArgumentParser(description="Seed invoicedb with sample data.")
    parser.add_argument(
        "--db",
        default="sample.sqlite",
        help="Path to the SQLite database file."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the existing database file first."
    )
    return parser.parse_args()

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(cursor) -> None:
    schema.create_customer_schema(cursor)
    schema.create_invoice_schema(cursor)

def seed_customers(cursor) -> dict[str, int]:
    john_id = customers.create_customer(
        cursor,
        name="John Doe",
        email="john@example.com",
    )
    alice_id = customers.create_customer(
        cursor,
        name="Alice Johnson",
        email="alice@example.com",
    )
    return {"john": john_id, "alice": alice_id}

def seed_invoices(cursor, customer_ids: dict[str, int]) -> dict[str, int]:
    today = date.today()
    issued_date = (today - timedelta(days=30)).isoformat()

    past_due = (today - timedelta(days=10)).isoformat()
    due_today = today.isoformat()
    future_due = (today + timedelta(days=10)).isoformat()

    john_id = customer_ids["john"]
    alice_id = customer_ids["alice"]

    john_draft = invoices.add_invoice_to_customer(
        cursor,
        customer_id=john_id,
        total=250,
        status="draft",
    )

    john_sent_overdue = invoices.add_invoice_to_customer(
        cursor,
        customer_id=john_id,
        total=1000,
        date_issued=issued_date,
        date_due=past_due,
        status="draft",
    )

    alice_paid = invoices.add_invoice_to_customer(
        cursor,
        customer_id=alice_id,
        total=400.25,
        date_issued=issued_date,
        date_due=past_due,
        status="draft",
    )

    alice_void = invoices.add_invoice_to_customer(
        cursor,
        customer_id=alice_id,
        total=750,
        date_issued=issued_date,
        date_due=future_due,
        status="draft",
    )

    status_updates = [
        (john_sent_overdue, "sent"),
        (alice_paid, "paid"),
        (alice_void, "void")
    ]

    for invoice_id, status in status_updates:
        cursor.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (status, invoice_id),
        )
    
    return {
        "john_draft": john_draft,
        "john_sent_overdue": john_sent_overdue,
        "alice_paid": alice_paid,
        "alice_void": alice_void,
    }

def main():
    args = parse_args()
    db_path = Path(args.db)

    if db_path.exists():
        if not args.force:
            raise SystemExit(
                f"Database already exists: {db_path}\n"
                f"Run again with --force to replace it."
            )
        db_path.unlink()

    conn = get_connection(str(db_path))
    try:
        cursor = conn.cursor()
        init_db(cursor)

        customer_ids = seed_customers(cursor)
        invoice_ids = seed_invoices(cursor, customer_ids)

        conn.commit()

        print(f"Seeded database: {db_path}")
        print("Customers:")
        print(f"  - John Doe (id={customer_ids['john']})")
        print(f"  - Alice Johnson (id={customer_ids['alice']})")
        print("Invoices:")
        print(f"  - John: draft (id={invoice_ids['john_draft']})")
        print(f"  - John: sent overdue (id={invoice_ids['john_sent_overdue']})")
        print(f"  - Alice: paid (id={invoice_ids['alice_paid']})")
        print(f"  - Alice: void (id={invoice_ids['alice_void']})")

    finally:
        conn.close()

if __name__ == "__main__":
    main()