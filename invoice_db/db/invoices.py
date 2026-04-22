from datetime import date, timedelta

from .customers import assert_customer_exists, get_customer_id_by_email
from .validators import validate_total, validate_status, validate_sort
from .utils import to_iso, to_cents

# Create
def add_invoice_to_customer(cursor, customer_id: int, date_issued: str = None, total: int = 0, date_due: str = None, status: str = "draft") -> int:
    """Attach a new invoice to an existing customer with customer_id."""
    assert_customer_exists(cursor, customer_id)
    validate_total(total)
    date_issued = to_iso(date_issued)
    date_due = to_iso(date_due)
    total = to_cents(total)
    validate_status(status)

    if status != "draft":
        raise ValueError("New invoices must start in draft status.")
    if (date_issued is not None and date_due is not None):
        if (date_issued > date_due):
            raise ValueError("Due date must be later than the date issued.")

    cursor.execute("""
        INSERT INTO invoices (customer_id, date_issued, date_due, total, status)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, date_issued, date_due, total, status))
    return cursor.lastrowid

# READ
def get_invoice_by_id(cursor, invoice_id: int) -> dict:
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    return cursor.fetchone()

def get_invoices_by_email(cursor, email: str) -> dict:
    """Fetch all invoices belonging to a customer identified by their email"""
    customer_id = get_customer_id_by_email(cursor, email)
    if customer_id is None:
        return []
    return get_invoices_by_customer_id(cursor, customer_id)

def get_invoices_by_customer_id(cursor, customer_id: int) -> list:
    cursor.execute("""
    SELECT id, customer_id, date_issued, date_due, total, created_at, updated_at, status
    FROM invoices
    WHERE customer_id = ?
    ORDER BY date_issued DESC, id DESC
    """, (customer_id,))
    return cursor.fetchall()

def get_invoices_by_customer_and_range(cursor, customer_id: int, start_date: str, end_date: str) -> list:
    start_date = to_iso(start_date)
    end_date = to_iso(end_date)
    cursor.execute("""
    SELECT id, customer_id, date_issued, date_due, total, created_at, updated_at, status
    FROM invoices
    WHERE customer_id = ? AND date_issued BETWEEN ? AND ?
    ORDER BY date_issued DESC, id DESC
    """, (customer_id, start_date, end_date,))
    return cursor.fetchall()

def count_invoices(
    cursor,
    customer_id: int | None = None,
    status: str | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
) -> int:
    query = ("SELECT COUNT(*) AS invoice_count FROM invoices")
    clauses = []
    params = []

    if customer_id is not None:
        clauses.append("customer_id = ?")
        params.append(customer_id)
    if status is not None:
        status = status.strip().lower()
        clauses.append("status = ?")
        params.append(status)
    if min_total is not None:
        clauses.append("total >= ?")
        params.append(to_cents(min_total))
    if max_total is not None:
        clauses.append("total <= ?")
        params.append(to_cents(max_total))

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    cursor.execute(query, params)
    row = cursor.fetchone()
    return row["invoice_count"] if row else 0

def list_invoices(
    cursor, 
    customer_id: int | None = None,
    status: str | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
    limit: int = 100, offset: int = 0,
    sort_by: str = "created_at",
    desc: bool = True
) -> list:
    sort_columns = {
        "id": "i.id",
        "date_issued": "i.date_issued", 
        "date_due": "i.date_due",
        "total": "i.total", 
        "status": "i.status",
        "created_at" : "i.created",
    }
    validate_sort(sort_by, sort_columns)
    validate_status(status)
    direction = "DESC" if desc else "ASC"

    sql = """
    SELECT 
        i.id,
        i.customer_id, 
        i.date_issued, 
        i.date_due, 
        i.total, 
        i.created_at, 
        i.updated_at, 
        i.status
    FROM invoices i
    """

    clauses, params = [], []

    if customer_id is not None:
        clauses.append("i.customer_id = ?")
        params.append(customer_id)
    if status is not None:
        status = status.strip().lower()
        clauses.append("i.status = ?")
        params.append(status)
    if min_total is not None:
        clauses.append("i.total >= ?")
        params.append(to_cents(min_total))
    if max_total is not None:
        clauses.append("i.total <= ?")
        params.append(to_cents(max_total))

    if clauses:
        sql += "WHERE " + " AND ".join(clauses)

    sql += f"""
    ORDER BY {sort_by} {direction}, id DESC
    LIMIT ? 
    OFFSET ?
    """

    params.extend([limit, offset])

    cursor.execute(sql, params)
    return cursor.fetchall()

def list_overdue_invoices(
    cursor,
    customer_id: int | None = None,
    days_overdue: int | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "date_due",
    desc: bool = True
) -> list:
    allowed_sort = {
        "id": "i.id",
        "date_issued": "i.date_issued", 
        "date_due": "i.date_due",
        "total": "i.total", 
        "days_overdue": "CAST(julianday(date('now')) - julianday(i.date_due) AS INTEGER)",
    }
    validate_sort(sort_by, allowed_sort)
    direction = "DESC" if desc else "ASC"

    sql = """
    SELECT
        i.id,
        i.customer_id,
        i.date_issued,
        i.date_due,
        i.total,
        i.status,
        i.created_at,
        i.updated_at,
        CAST(julianday(date('now', 'localtime')) - julianday(i.date_due) AS INTEGER) AS days_overdue
    FROM
        invoices i
    """

    clauses = ["i.status = ?",
               "i.date_due IS NOT NULL",
                "i.date_due < date('now', 'localtime')",
    ] 
    params = ["sent"]

    if customer_id is not None:
        clauses.append("i.customer_id = ?")
        params.append(customer_id)
    if days_overdue is not None:
        clauses.append("julianday(date('now', 'localtime')) - julianday(i.date_due) >= ?")
        params.append(days_overdue)
    if min_total is not None:
        clauses.append("i.total >= ?")
        params.append(to_cents(min_total))
    if max_total is not None:
        clauses.append("i.total <= ?")
        params.append(to_cents(max_total))

    sql += "WHERE " + " AND ".join(clauses)
    sql += f"""
    ORDER BY  {sort_by} {direction}, id DESC
    LIMIT ?
    OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(sql, params)
    return cursor.fetchall()


def sum_invoices_by_customer(cursor, customer_id: int) -> int:
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_sum
        FROM invoices
        WHERE customer_id = ?
    """, (customer_id,))
    return cursor.fetchone()['total_sum']


# UPDATE
def update_invoice(
        cursor,
        invoice_id: int, 
        *, 
        date_issued: int = None, 
        date_due: int = None, 
        total: int = None, 
        customer_id: int = None
) -> bool:
    
    invoice = get_invoice_by_id(cursor, invoice_id)
    if not invoice:
        return False

    updates, params = [], []
    
    new_date_issued = to_iso(date_issued) if date_issued is not None else invoice["date_issued"]
    new_date_due = to_iso(date_due) if date_due is not None else invoice["date_due"]

    if new_date_issued is not None and new_date_due is not None:
        if new_date_due < new_date_issued:
            raise ValueError("Due date must be later than or equal to date issued.")

    if date_issued:
        updates.append("date_issued = ?")
        params.append(new_date_issued)
    if date_due:
        updates.append("date_due = ?")
        params.append(new_date_due)
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
    query = f"UPDATE invoices SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

def set_invoice_status(cursor, invoice_id: int, status: str) -> bool:
    cursor.execute(
        "SELECT status, date_issued, date_due FROM invoices WHERE id = ?",
        (invoice_id,),
    )
    row = cursor.fetchone()

    if row is None:
        raise ValueError("Invoice not found")
    
    current_status = row['status']
    date_issued = row['date_issued']
    date_due = (row['date_due'])
    today = date.today().isoformat()

    if status == current_status:
        return True

    status_transitions = {
        "draft": {"sent"},
        "sent": {"paid", "void"},
        "paid": {"sent"},
        "void": set(),
    }

    if status not in status_transitions.get(current_status, set()):
        raise ValueError(f"Invalid transition {current_status} -> {status}")
    
    if current_status == "draft" and status == "sent":
        if date_issued is None:
            date_issued = date.today().isoformat()
        if date_due is None:
            date_due = (date.fromisoformat(date_issued) + timedelta(days=30)).isoformat()
        if date_due < date_issued:
            raise ValueError(
                "Date issued and date due must be future dates, and due date must be on or after date issued."
            )

    cursor.execute(
        """
        UPDATE
            invoices 
        SET 
            status = ?,
            date_issued = COALESCE(?, date_issued),
            date_due = COALESCE(?, date_due)
        WHERE 
            id = ? 
        """,
        (status, date_issued, date_due, invoice_id)
        )
    return cursor.rowcount > 0

# DELETE
def delete_invoice(cursor, invoice_id: int) -> bool:
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    return cursor.rowcount > 0