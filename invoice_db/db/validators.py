import re

EMAIL_RE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Z-a-z' -]*[A-Za-z]$")

# Customer
def normalize_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Name cannot be empty.")
    name = " ".join(name.strip().split()).title()
    if not NAME_RE.match(name):
        raise ValueError("Invalid name format: only letters, spaces, apostrophes, and hyphens are allowed.")
    return name

def normalize_email(email: str) -> str:
    if not email or not isinstance(email, str):
        raise ValueError("Email cannot be empty.")
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Invalid email format")
    return email

# Invoices
def validate_total(amount: int | float) -> int:
    if amount is None:
        raise ValueError("Invoice total is required.")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Invoice total must be a valid number.")
    if amount < 0:
        raise ValueError("Invoice total cannot be negative.")
    return amount

def validate_status(status: str | None) -> None:
    ALLOWED_STATUSES = {"draft", "sent", "paid", "void"}

    if status is not None:
        status = status.strip().lower()
    else:
        return

    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    
def validate_sort(sort_by: str, allowed: set[str]) -> None:
    if sort_by not in allowed:
        raise ValueError(f"Invalid sort column: {sort_by}")

def normalize_status(status: str | None, allowed: set[str] | None = None) -> str | None:
    allowed = allowed or {"draft", "sent", "paid", "void"}
    if status is None:
        return None

    status = status.strip().lower()
    if status == "":
        return None

    if status not in allowed:
        raise ValueError(f"Invoice status must be one of: {', '.join(sorted(allowed))}.")

    return status

def validate_positive_id(value: int | None, label: str) -> None:
    if value is None:
        return
    if value <= 0:
        raise ValueError(f"{label} must be a positive integer.")

def validate_positive_total(total: int | float) -> None:
    if total <= 0:
        raise ValueError("Invoice total must be greater than 0.")

def validate_total_range(min_total: int | float | None = None, max_total: int | float | None = None) -> None:
    if min_total is not None and min_total < 0:
        raise ValueError("Minimum total cannot be negative.")

    if max_total is not None and max_total < 0:
        raise ValueError("Maximum total cannot be negative.")

    if min_total is not None and max_total is not None and min_total > max_total:
        raise ValueError("Minimum total cannot be greater than maximum total.")

def validate_pagination(limit: int, offset: int) -> None:
    if limit <= 0:
        raise ValueError("Limit must be greater than 0.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

def normalize_sort_by(sort_by: str, allowed_fields: set[str]) -> str:
    sort_by = sort_by.strip().lower()

    if sort_by == "":
        raise ValueError("Sort field cannot be empty.")

    if sort_by not in allowed_fields:
        allowed = ", ".join(sorted(allowed_fields))
        raise ValueError(f"Sort field must be one of: {allowed}.")

    return sort_by

# Products
def normalize_product_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Product name cannot be empty.")
    name = " ".join(name.strip().split())
    if not name:
        raise ValueError("Product name cannot be empty.")
    return name

def normalize_description(description: str | None) -> str | None:
    if description is None:
        return None
    description = " ".join(description.strip().split())
    return description or None

def validate_unit_price_cents(unit_price_cents: int) -> int:
    if unit_price_cents is None:
        raise ValueError("Product unit price is required.")
    try:
        unit_price_cents = int(unit_price_cents)
    except (TypeError, ValueError):
        raise ValueError("Product unit price must be a valid integer.")
    if unit_price_cents < 0:
        raise ValueError("Product unit price cannot be negative.")
    return unit_price_cents

def normalize_is_active(is_active: bool | int) -> int:
    if isinstance(is_active, bool):
        return int(is_active)
    if is_active in (0, 1):
        return is_active
    raise ValueError("Product active flag must be true or false.")
