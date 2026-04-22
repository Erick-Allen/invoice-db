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

def validate_status(status: str) -> None:
    ALLOWED_STATUSES = {"draft", "sent", "paid", "void"}

    if status:
        status = status.strip().lower()
    else:
        return

    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    
def validate_sort(sort_by: str, allowed: set[str]) -> None:
    if sort_by not in allowed:
        raise ValueError(f"Invalid sort column: {sort_by}")
