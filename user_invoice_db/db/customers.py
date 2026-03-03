import sqlite3
from .validators import normalize_name, normalize_email

# Create
def create_customer(cursor, name, email):
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
def get_customer_by_id(cursor, customer_id):
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    return cursor.fetchone()

def get_customer_by_email(cursor, email):
    cursor.execute("SELECT * FROM customers WHERE lower(email) = lower(?)", (email,))
    return cursor.fetchone()

def get_customer_id_by_email(cursor, email):
    row = get_customer_by_email(cursor, email)
    return row['id'] if row else None


# Update
def update_customer(cursor, customer_id, name=None, email=None):
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
def delete_customer(cursor, customer_id):
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