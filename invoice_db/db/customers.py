import sqlite3
from .validators import normalize_name, normalize_email
from .utils import to_cents

# Create
def create_customer(cursor, name: str, email: str) -> int:
    name = normalize_name(name)
    email = normalize_email(email)
    assert_email_unique(cursor, email)
    try:
        cursor.execute("""
            INSERT INTO customers (name, email) 
            VALUES (?, ?)
        """, (name, email))
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise ValueError("Email already exists") from e

# Read
def get_customer_by_id(cursor, customer_id: int) -> dict:
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    return cursor.fetchone()

def get_customer_by_email(cursor, email: str) -> dict:
    cursor.execute("SELECT * FROM customers WHERE lower(email) = lower(?)", (email,))
    return cursor.fetchone()

def get_customer_id_by_email(cursor, email: str) -> int:
    row = get_customer_by_email(cursor, email)
    return row['id'] if row else None

def get_customers(cursor, min_total_dollars: int = 0) -> list:
    min_cents = to_cents(min_total_dollars)
    cursor.execute("""
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            COALESCE(SUM(i.total), 0) AS total
        FROM customers c
        LEFT JOIN invoices i ON i.customer_id = c.id
        GROUP BY c.id, c.name, c.email
        HAVING COALESCE(SUM(i.total), 0) >= ?
        ORDER BY c.id
    """, (min_cents,))
    return cursor.fetchall()

def get_customer_invoice_summary(cursor) -> list:
    """Return a list of customers with their invoice counts and total from view customer_invoice_summary"""
    cursor.execute("SELECT * FROM customer_invoice_summary ORDER BY customer_id")
    return cursor.fetchall()


# Update
def update_customer(cursor, customer_id: int, name: str = None, email: str = None) -> bool:
    updates, params = [], []

    if name:
        updates.append("name = ?")
        params.append(normalize_name(name))
    if email:
        assert_email_unique(cursor, email, exclude_customer_id=customer_id)
        updates.append("email = ?")
        params.append(normalize_email(email))

    if not updates:
        return False # nothing to update
    
    params.append(customer_id)
    query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

# Delete
def delete_customer(cursor, customer_id: int) -> bool:
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    return cursor.rowcount > 0


# Assertions
def assert_customer_exists(cursor, customer_id: int) -> None:
    row = cursor.execute("SELECT 1 FROM customers WHERE id=?", (customer_id,)).fetchone()
    if not row:
        raise ValueError (f"Customer not found (id={customer_id})")
    
def assert_email_unique(cursor, email: str, exclude_customer_id: int | None = None) -> None:
    email = email.strip().lower()
    row = cursor.execute(
        "SELECT id FROM customers WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if row and (exclude_customer_id is None or row['id'] != exclude_customer_id):
        raise ValueError(f"Email '{(email)}' already exists.")