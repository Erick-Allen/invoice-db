import sqlite3
from invoice_db.db import customers as customers_db
from typing import TypedDict
from . import exceptions

class CustomerRecord(TypedDict):
    id: int
    name: str
    email: str
    
def _to_customer_record(row: sqlite3.Row) -> CustomerRecord:
    return dict(row)

def _validate_positive_id(customer_id: int) -> None:
    if customer_id <= 0:
        raise exceptions.ValidationError("Customer id must be a positive integer.")
    
def _require_customer_by_id(cursor, customer_id: int) -> sqlite3.Row:
    _validate_positive_id(customer_id)

    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")
    
    return customer

def _require_customer_by_email(cursor, customer_email: str) -> None:
    customer_email = _normalize_customer_email(customer_email)
    customer = customers_db.get_customer_by_email(cursor, customer_email)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (email={customer_email})")
    
    return customer

def _prepare_customer_changes(
        customer: sqlite3.Row, 
        new_name: str | None = None,
        new_email: str | None = None,
) -> tuple[str | None, str | None]:
    if new_name is None and new_email is None:
        raise exceptions.ValidationError("Please provide a new name and/or new email.")

    normalized_name = None if new_name is None else _normalize_customer_name(new_name)
    normalized_email = None if new_email is None else _normalize_customer_email(new_email)

    if (
        (normalized_name is None or normalized_name == customer['name']) and 
        (normalized_email is None or normalized_email == customer['email'])
    ):
        raise exceptions.ValidationError("No changes detected.")
    
    return normalized_name, normalized_email

def _update_customer(
    cursor, 
    customer: sqlite3.Row, 
    new_name: str | None = None, 
    new_email: str | None = None
) -> sqlite3.Row:
    normalized_name, normalized_email = _prepare_customer_changes(customer, new_name, new_email)

    try:
        updated = customers_db.update_customer(cursor, customer['id'], normalized_name, normalized_email)
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError(
            f"Customer email already exists ({normalized_email})"
        ) from e 

    if not updated:
        raise exceptions.ServiceError(f"Failed to update customer {customer['id']}.")
 
    updated_customer = customers_db.get_customer_by_id(cursor, customer['id'])
    if updated_customer is None:
        raise exceptions.ServiceError("Updated customer, but failed to reload record.")
    
    return updated_customer

def _normalize_customer_name(customer_name: str) -> str:
    customer_name = customer_name.strip()
    if customer_name == "":
        raise exceptions.ValidationError(f"Customer name cannot be empty.")
    return customer_name

def _normalize_customer_email(customer_email: str) -> str:
    customer_email = customer_email.strip()
    if customer_email == "":
        raise exceptions.ValidationError(f"Customer email cannot be empty.")    
    return customer_email

#CRUD
def create_customer(cursor, customer_name: str, customer_email: str) -> CustomerRecord:
    customer_name = _normalize_customer_name(customer_name)
    customer_email = _normalize_customer_email(customer_email)

    try:
        customer_id = customers_db.create_customer(cursor, customer_name, customer_email)
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError(
            f"Customer email already exists ({customer_email})"
        ) from e

    if customer_id is None:
        raise exceptions.ServiceError("Failed to create customer.")
    
    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.ServiceError("Customer was created but could not be retrieved.")
    
    return _to_customer_record(customer)

def get_customer_by_id(cursor, customer_id: int) -> CustomerRecord:
    customer = _require_customer_by_id(cursor, customer_id)
    return _to_customer_record(customer)

def get_customer_by_email(cursor, customer_email: str) -> CustomerRecord:
    customer = _require_customer_by_email(cursor, customer_email)
    return _to_customer_record(customer)

def list_customers(cursor) -> list[CustomerRecord]:
    customers = customers_db.get_customers(cursor)
    return [_to_customer_record(customer) for customer in customers]

def update_customer_by_id(
    cursor, 
    customer_id: int,
    new_name: str | None = None,
    new_email: str | None = None,
    ) -> CustomerRecord: 
    customer = _require_customer_by_id(cursor, customer_id)
    return _to_customer_record(_update_customer(cursor, customer, new_name, new_email))

def update_customer_by_email(
    cursor,
    customer_email: str,
    new_name: str | None = None,
    new_email: str | None = None,
    ) -> CustomerRecord: 
    customer = _require_customer_by_email(cursor, customer_email)
    updated_customer = _update_customer(cursor, customer, new_name, new_email)
    return _to_customer_record(updated_customer)

def delete_customer_by_id(cursor, customer_id: int) -> None:
    _validate_positive_id(customer_id)
    deleted_customer = customers_db.delete_customer(cursor, customer_id=customer_id)
    
    if not deleted_customer:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")