from .customers import assert_customer_exists, get_customer_id_by_email
from .validators import validate_total
from .utils import to_iso, to_cents

# Create
def add_invoice_to_customer(cursor, customer_id, date_issued, total, date_due=None):
    """Attach a new invoice to an existing customer with customer_id."""
    assert_customer_exists(cursor, customer_id)
    validate_total(total)
    date_issued = to_iso(date_issued)
    date_due = to_iso(date_due)
    total = to_cents(total)

    cursor.execute("""
        INSERT INTO invoices (customer_id, date_issued, date_due, total)
        VALUES (?, ?, ?, ?)
    """, (customer_id, date_issued, date_due, total))
    return cursor.lastrowid

# READ
def get_invoice_by_id(cursor, invoice_id):
    cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
    return cursor.fetchone()

def get_invoices_by_email(cursor, email):
    """Fetch all invoices belonging to a customer identified by their email"""
    customer_id = get_customer_id_by_email(cursor, email)
    if customer_id is None:
        return []
    return get_invoices_by_customer_id(cursor, customer_id)

def get_invoices_by_customer_id(cursor, customer_id):
    cursor.execute("""
    SELECT invoice_id, customer_id, date_issued, date_due, total, created_at, updated_at
    FROM invoices
    WHERE customer_id = ?
    ORDER BY date_issued DESC, invoice_id DESC
    """, (customer_id,))
    return cursor.fetchall()

def get_invoices_by_customer_and_range(cursor, customer_id, start_date, end_date):
    start_date = to_iso(start_date)
    end_date = to_iso(end_date)
    cursor.execute("""
    SELECT invoice_id, customer_id, date_issued, date_due, total, created_at, updated_at
    FROM invoices
    WHERE customer_id = ? AND date_issued BETWEEN ? AND ?
    ORDER BY date_issued DESC, invoice_id DESC
    """, (customer_id, start_date, end_date,))
    return cursor.fetchall()

def count_invoices(cursor):
    cursor.execute("SELECT COUNT(*) AS invoice_count FROM invoices")
    return cursor.fetchone()['invoice_count']

def count_invoices_by_customer(cursor, customer_id):
    cursor.execute("SELECT COUNT(*) AS count FROM invoices WHERE customer_id = ?",
    (customer_id,)
    )
    row = cursor.fetchone()
    return row["count"] if row else 0

def list_invoices(cursor, limit=100, offset=0):
    cursor.execute("""
    SELECT invoice_id, customer_id, date_issued, date_due, total, created_at, updated_at
    FROM invoices
    ORDER BY date_issued DESC, invoice_id DESC
    LIMIT ? OFFSET ?
    """, (limit, offset))
    return cursor.fetchall()

def sum_invoices_by_customer(cursor, customer_id):
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_sum
        FROM invoices
        WHERE customer_id = ?
    """, (customer_id,))
    return cursor.fetchone()['total_sum']

# UPDATE
def update_invoice(cursor, invoice_id, *, date_issued=None, date_due=None, total=None, customer_id=None):
    updates, params = [], []
    
    if date_issued:
        updates.append("date_issued = ?")
        params.append(to_iso(date_issued))
    if date_due:
        updates.append("date_due = ?")
        params.append(to_iso(date_due))
    if total:
        validate_total(total)
        updates.append("total = ?")
        params.append(to_cents(total))
    if  customer_id:
        assert_customer_exists(cursor, customer_id)
        updates.append("customer_id = ?")
        params.append(customer_id)

    if not updates:
        return False
    
    params.append(invoice_id)
    query = f"UPDATE invoices SET {', '.join(updates)} WHERE invoice_id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

# DELETE
def delete_invoice(cursor, invoice_id):
    cursor.execute("DELETE FROM invoices WHERE invoice_id= ?", (invoice_id,))
    return cursor.rowcount > 0