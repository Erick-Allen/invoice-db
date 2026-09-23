from dataclasses import dataclass
from sqlite3 import Row

from .validators import (
    normalize_customer_phone,
    normalize_customer_type,
    normalize_email,
    normalize_is_active,
    normalize_name,
    normalize_optional_customer_text,
)


@dataclass
class CustomerCreate:
    name: str
    email: str
    phone: str | None = None
    customer_type: str = "residential"
    company_name: str | None = None
    is_active: bool = True


@dataclass
class Customer:
    id: int
    name: str
    email: str
    phone: str | None
    customer_type: str
    company_name: str | None
    is_active: bool
    created_at: str
    updated_at: str
    total_cents: int | None = None


def _to_customer(row: Row) -> Customer:
    return Customer(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        customer_type=row["customer_type"],
        company_name=row["company_name"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        total_cents=row["total"] if "total" in row.keys() else None,
    )


def _normalize_company_name(company_name: str | None, customer_type: str) -> str | None:
    if customer_type == "residential":
        return None
    return normalize_optional_customer_text(company_name)


# Create
def create_customer(
    cursor,
    name: str,
    email: str,
    phone: str | None = None,
    customer_type: str = "residential",
    company_name: str | None = None,
    is_active: bool = True,
) -> int:
    customer = CustomerCreate(
        name=name,
        email=email,
        phone=phone,
        customer_type=customer_type,
        company_name=company_name,
        is_active=is_active,
    )
    name = normalize_name(customer.name)
    email = normalize_email(customer.email)
    phone = normalize_customer_phone(customer.phone)
    customer_type = normalize_customer_type(customer.customer_type)
    company_name = _normalize_company_name(customer.company_name, customer_type)
    is_active = normalize_is_active(customer.is_active)

    cursor.execute(
        """
        INSERT INTO customers (name, email, phone, customer_type, company_name, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, email, phone, customer_type, company_name, is_active),
    )

    return cursor.lastrowid


# Read
def get_customer_by_id(cursor, customer_id: int) -> Customer | None:
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    return _to_customer(row) if row else None


def get_customer_by_email(cursor, email: str) -> Customer | None:
    cursor.execute("SELECT * FROM customers WHERE lower(email) = lower(?)", (email,))
    row = cursor.fetchone()
    return _to_customer(row) if row else None


def get_customer_id_by_email(cursor, email: str) -> int | None:
    customer = get_customer_by_email(cursor, email)
    return customer.id if customer else None


def get_customers(cursor, min_total_cents: int = 0, active_only: bool = False) -> list[Customer]:
    sql = """
        SELECT
            c.id,
            c.name,
            c.email,
            c.phone,
            c.customer_type,
            c.company_name,
            c.is_active,
            c.created_at,
            c.updated_at,
            COALESCE(SUM(i.total), 0) AS total
        FROM customers c
        LEFT JOIN invoices i ON i.customer_id = c.id
    """
    params = []

    if active_only:
        sql += " WHERE c.is_active = ?"
        params.append(1)

    sql += """
        GROUP BY c.id, c.name, c.email, c.phone, c.customer_type, c.company_name, c.is_active, c.created_at, c.updated_at
        HAVING COALESCE(SUM(i.total), 0) >= ?
        ORDER BY c.id
    """
    params.append(min_total_cents)

    cursor.execute(sql, params)
    return [_to_customer(row) for row in cursor.fetchall()]


def get_customer_invoice_summary(cursor) -> list:
    """Return customers with invoice counts and totals from customer_invoice_summary."""
    cursor.execute("SELECT * FROM customer_invoice_summary ORDER BY customer_id")
    return cursor.fetchall()


# Update
def update_customer(
    cursor,
    customer_id: int,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    customer_type: str | None = None,
    company_name: str | None = None,
    is_active: bool | None = None,
) -> Customer | None:
    updates, params = [], []

    customer = get_customer_by_id(cursor, customer_id)
    if customer is None:
        return None

    next_customer_type = customer.customer_type

    if name is not None:
        updates.append("name = ?")
        params.append(normalize_name(name))
    if email is not None:
        assert_email_unique(cursor, email, exclude_customer_id=customer_id)
        updates.append("email = ?")
        params.append(normalize_email(email))
    if phone is not None:
        updates.append("phone = ?")
        params.append(normalize_customer_phone(phone))
    if customer_type is not None:
        next_customer_type = normalize_customer_type(customer_type)
        updates.append("customer_type = ?")
        params.append(next_customer_type)
    if company_name is not None or customer_type is not None:
        updates.append("company_name = ?")
        params.append(_normalize_company_name(company_name if company_name is not None else customer.company_name, next_customer_type))
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(normalize_is_active(is_active))

    if not updates:
        return customer

    params.append(customer_id)
    query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))

    return get_customer_by_id(cursor, customer_id)


# Delete
def delete_customer(cursor, customer_id: int) -> bool:
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    return cursor.rowcount > 0


# Assertions
def assert_customer_exists(cursor, customer_id: int) -> None:
    if get_customer_by_id(cursor, customer_id) is None:
        raise ValueError(f"Customer not found (id={customer_id})")


def assert_email_unique(cursor, email: str, exclude_customer_id: int | None = None) -> None:
    email = email.strip().lower()
    row = cursor.execute(
        "SELECT id FROM customers WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if row and (exclude_customer_id is None or row["id"] != exclude_customer_id):
        raise ValueError(f"Email '{email}' already exists.")
