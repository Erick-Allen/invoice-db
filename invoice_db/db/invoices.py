from .customers import assert_customer_exists, get_customer_id_by_email
from .validators import validate_total, validate_status, validate_sort
from ..utils import to_iso

def _next_invoice_number(cursor, workspace_id: int | None = None) -> int:
    if workspace_id is None:
        cursor.execute(
            """
            SELECT COALESCE(MAX(invoice_number), 0) + 1 AS next_invoice_number
            FROM invoices
            WHERE workspace_id IS NULL
            """
        )
    else:
        cursor.execute(
            """
            SELECT COALESCE(MAX(invoice_number), 0) + 1 AS next_invoice_number
            FROM invoices
            WHERE workspace_id = ?
            """,
            (workspace_id,),
        )

    return cursor.fetchone()["next_invoice_number"]

# Create
def add_invoice_to_customer(
    cursor,
    customer_id: int,
    date_issued: str = None,
    total: int = 0,
    subtotal_cents: int | None = None,
    tax_rate: str | None = None,
    tax_cents: int = 0,
    date_due: str = None,
    status: str = "draft",
    location_id: int | None = None,
    title: str | None = None,
    description: str | None = None,
    workspace_id: int | None = None,
) -> int:
    """Attach a new invoice to an existing customer with customer_id."""
    assert_customer_exists(cursor, customer_id, workspace_id=workspace_id)
    validate_total(total)
    date_issued = to_iso(date_issued)
    date_due = to_iso(date_due)
    validate_status(status)

    if (date_issued is not None and date_due is not None):
        if (date_issued > date_due):
            raise ValueError("Due date must be later than the date issued.")

    invoice_number = _next_invoice_number(cursor, workspace_id=workspace_id)

    if subtotal_cents is None:
        subtotal_cents = total

    cursor.execute("""
        INSERT INTO invoices (
            workspace_id,
            invoice_number,
            customer_id,
            location_id,
            title,
            description,
            date_issued,
            date_due,
            subtotal_cents,
            tax_rate,
            tax_cents,
            total,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        workspace_id,
        invoice_number,
        customer_id,
        location_id,
        title,
        description,
        date_issued,
        date_due,
        subtotal_cents,
        tax_rate,
        tax_cents,
        total,
        status,
    ))
    return cursor.lastrowid

# READ
def get_invoice_by_id(cursor, invoice_id: int, workspace_id: int | None = None) -> dict:
    if workspace_id is None:
        cursor.execute(
            "SELECT * FROM invoices WHERE id = ? AND workspace_id IS NULL",
            (invoice_id,),
        )
    else:
        cursor.execute(
            "SELECT * FROM invoices WHERE id = ? AND workspace_id = ?",
            (invoice_id, workspace_id),
        )
    return cursor.fetchone()

def get_invoices_by_email(cursor, email: str, workspace_id: int | None = None) -> dict:
    """Fetch all invoices belonging to a customer identified by their email"""
    customer_id = get_customer_id_by_email(cursor, email, workspace_id=workspace_id)
    if customer_id is None:
        return []
    return get_invoices_by_customer_id(cursor, customer_id, workspace_id=workspace_id)

def get_invoices_by_customer_id(cursor, customer_id: int, workspace_id: int | None = None) -> list:
    workspace_clause = "workspace_id IS NULL" if workspace_id is None else "workspace_id = ?"
    params = (customer_id,) if workspace_id is None else (customer_id, workspace_id)
    cursor.execute("""
    SELECT id, invoice_number, customer_id, location_id, title, description, date_issued, date_due, subtotal_cents, tax_rate, tax_cents, total, created_at, updated_at, status
    FROM invoices
    WHERE customer_id = ? AND """ + workspace_clause + """
    ORDER BY date_issued DESC, id DESC
    """, params)
    return cursor.fetchall()

def get_invoices_by_customer_and_range(
    cursor,
    customer_id: int,
    start_date: str,
    end_date: str,
    workspace_id: int | None = None,
) -> list:
    start_date = to_iso(start_date)
    end_date = to_iso(end_date)
    workspace_clause = "workspace_id IS NULL" if workspace_id is None else "workspace_id = ?"
    params = (
        (customer_id, start_date, end_date)
        if workspace_id is None
        else (customer_id, start_date, end_date, workspace_id)
    )
    cursor.execute("""
    SELECT id, invoice_number, customer_id, location_id, title, description, date_issued, date_due, subtotal_cents, tax_rate, tax_cents, total, created_at, updated_at, status
    FROM invoices
    WHERE customer_id = ? AND date_issued BETWEEN ? AND ? AND """ + workspace_clause + """
    ORDER BY date_issued DESC, id DESC
    """, params)
    return cursor.fetchall()

def count_invoices(
    cursor,
    customer_id: int | None = None,
    status: str | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
    workspace_id: int | None = None,
) -> int:
    query = ("SELECT COUNT(*) AS invoice_count FROM invoices")
    clauses = []
    params = []

    if customer_id is not None:
        clauses.append("customer_id = ?")
        params.append(customer_id)
    if workspace_id is None:
        clauses.append("workspace_id IS NULL")
    else:
        clauses.append("workspace_id = ?")
        params.append(workspace_id)
    if status is not None:
        status = status.strip().lower()
        clauses.append("status = ?")
        params.append(status)
    if min_total is not None:
        clauses.append("total >= ?")
        params.append(min_total)
    if max_total is not None:
        clauses.append("total <= ?")
        params.append(max_total)

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
    desc: bool = True,
    workspace_id: int | None = None,
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
        i.invoice_number,
        i.customer_id,
        i.location_id,
        i.title,
        i.description,
        i.date_issued, 
        i.date_due, 
        i.subtotal_cents,
        i.tax_rate,
        i.tax_cents,
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
    if workspace_id is None:
        clauses.append("i.workspace_id IS NULL")
    else:
        clauses.append("i.workspace_id = ?")
        params.append(workspace_id)
    if status is not None:
        status = status.strip().lower()
        clauses.append("i.status = ?")
        params.append(status)
    if min_total is not None:
        clauses.append("i.total >= ?")
        params.append(min_total)
    if max_total is not None:
        clauses.append("i.total <= ?")
        params.append(max_total)

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
    desc: bool = True,
    workspace_id: int | None = None,
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
        i.invoice_number,
        i.customer_id,
        i.location_id,
        i.title,
        i.description,
        i.date_issued,
        i.date_due,
        i.subtotal_cents,
        i.tax_rate,
        i.tax_cents,
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
    if workspace_id is None:
        clauses.append("i.workspace_id IS NULL")
    else:
        clauses.append("i.workspace_id = ?")
        params.append(workspace_id)
    if days_overdue is not None:
        clauses.append("julianday(date('now', 'localtime')) - julianday(i.date_due) >= ?")
        params.append(days_overdue)
    if min_total is not None:
        clauses.append("i.total >= ?")
        params.append(min_total)
    if max_total is not None:
        clauses.append("i.total <= ?")
        params.append(max_total)

    sql += "WHERE " + " AND ".join(clauses)
    sql += f"""
    ORDER BY  {sort_by} {direction}, id DESC
    LIMIT ?
    OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(sql, params)
    return cursor.fetchall()


def sum_invoices_by_customer(cursor, customer_id: int, workspace_id: int | None = None) -> int:
    workspace_clause = "workspace_id IS NULL" if workspace_id is None else "workspace_id = ?"
    params = (customer_id,) if workspace_id is None else (customer_id, workspace_id)
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_sum
        FROM invoices
        WHERE customer_id = ? AND """ + workspace_clause + """
    """, params)
    return cursor.fetchone()['total_sum']


# UPDATE
def update_invoice(
        cursor,
        invoice_id: int, 
        *, 
        title: str | None = None,
        update_title: bool = False,
        description: str | None = None,
        update_description: bool = False,
        date_issued: int = None, 
        date_due: int = None, 
        subtotal_cents: int | None = None,
        tax_rate: str | None = None,
        tax_cents: int | None = None,
        total: int = None, 
        customer_id: int = None,
        location_id: int | None = None,
        update_location: bool = False,
        workspace_id: int | None = None,
) -> bool:
    
    invoice = get_invoice_by_id(cursor, invoice_id, workspace_id=workspace_id)
    if not invoice:
        return False

    updates, params = [], []
    
    new_date_issued = to_iso(date_issued) if date_issued is not None else invoice["date_issued"]
    new_date_due = to_iso(date_due) if date_due is not None else invoice["date_due"]

    if new_date_issued is not None and new_date_due is not None:
        if new_date_due < new_date_issued:
            raise ValueError("Due date must be later than or equal to date issued.")

    if update_title:
        updates.append("title = ?")
        params.append(title)
    if update_description:
        updates.append("description = ?")
        params.append(description)
    if date_issued is not None:
        updates.append("date_issued = ?")
        params.append(new_date_issued)
    if date_due is not None:
        updates.append("date_due = ?")
        params.append(new_date_due)
    if total is not None:
        validate_total(total)
        updates.append("total = ?")
        params.append(total)
    if subtotal_cents is not None:
        validate_total(subtotal_cents)
        updates.append("subtotal_cents = ?")
        params.append(subtotal_cents)
    if tax_rate is not None:
        updates.append("tax_rate = ?")
        params.append(tax_rate)
    if tax_cents is not None:
        validate_total(tax_cents)
        updates.append("tax_cents = ?")
        params.append(tax_cents)
    if  customer_id is not None:
        assert_customer_exists(cursor, customer_id, workspace_id=workspace_id)
        updates.append("customer_id = ?")
        params.append(customer_id)
    if update_location:
        updates.append("location_id = ?")
        params.append(location_id)

    if not updates:
        return False
    
    params.append(invoice_id)
    query = f"UPDATE invoices SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

def set_invoice_status(cursor, invoice_id: int, status: str, workspace_id: int | None = None) -> bool:
    validate_status(status)
    if workspace_id is None:
        cursor.execute(
            "SELECT status FROM invoices WHERE id = ? AND workspace_id IS NULL",
            (invoice_id,),
        )
    else:
        cursor.execute(
            "SELECT status FROM invoices WHERE id = ? AND workspace_id = ?",
            (invoice_id, workspace_id),
        )
    row = cursor.fetchone()

    if row is None:
        raise ValueError("Invoice not found")
    
    if status == row["status"]:
        return True

    if workspace_id is None:
        cursor.execute(
            "UPDATE invoices SET status = ? WHERE id = ? AND workspace_id IS NULL",
            (status, invoice_id),
        )
    else:
        cursor.execute(
            "UPDATE invoices SET status = ? WHERE id = ? AND workspace_id = ?",
            (status, invoice_id, workspace_id),
        )
    return cursor.rowcount > 0

# DELETE
def delete_invoice(cursor, invoice_id: int, workspace_id: int | None = None) -> bool:
    if workspace_id is None:
        cursor.execute(
            "DELETE FROM invoices WHERE id = ? AND workspace_id IS NULL",
            (invoice_id,),
        )
    else:
        cursor.execute(
            "DELETE FROM invoices WHERE id = ? AND workspace_id = ?",
            (invoice_id, workspace_id),
        )
    return cursor.rowcount > 0
