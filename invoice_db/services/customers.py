import sqlite3
from typing import NotRequired, TypedDict

from invoice_db.db import customers as customers_db
from invoice_db.db.validators import (
    normalize_customer_phone,
    normalize_customer_type,
    normalize_email,
    normalize_is_active,
    normalize_name,
    normalize_optional_customer_text,
    validate_positive_id,
)
from . import exceptions

class CustomerRecord(TypedDict):
    id: int
    name: str
    email: str
    phone: str | None
    customer_type: str
    company_name: str | None
    is_active: bool
    created_at: str
    updated_at: str
    total: NotRequired[int]
    
def _to_customer_record(customer: customers_db.Customer) -> CustomerRecord:
    record: CustomerRecord = {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "customer_type": customer.customer_type,
        "company_name": customer.company_name,
        "is_active": customer.is_active,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }
    if customer.total_cents is not None:
        record["total"] = customer.total_cents
    return record

def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))
    
def _require_customer_by_id(cursor, customer_id: int) -> customers_db.Customer:
    try:
        validate_positive_id(customer_id, "Customer id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")
    
    return customer

def _require_customer_by_email(cursor, customer_email: str) -> customers_db.Customer:
    customer_email = _normalize_customer_email(customer_email)
    customer = customers_db.get_customer_by_email(cursor, customer_email)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (email={customer_email})")
    
    return customer

def _prepare_customer_changes(
        customer: customers_db.Customer, 
        new_name: str | None = None,
        new_email: str | None = None,
        new_phone: str | None = None,
        new_customer_type: str | None = None,
        new_company_name: str | None = None,
        new_is_active: bool | None = None,
) -> tuple[str | None, str | None, str | None, str | None, str | None, bool | None]:
    if (
        new_name is None
        and new_email is None
        and new_phone is None
        and new_customer_type is None
        and new_company_name is None
        and new_is_active is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the customer.")

    try:
        normalized_name = None if new_name is None else _normalize_customer_name(new_name)
        normalized_email = None if new_email is None else _normalize_customer_email(new_email)
        normalized_phone = None if new_phone is None else _normalize_customer_phone(new_phone)
        normalized_type = None if new_customer_type is None else normalize_customer_type(new_customer_type)
        effective_type = customer.customer_type if normalized_type is None else normalized_type
        normalized_company = (
            None
            if new_company_name is None
            else None if effective_type == "residential" else normalize_optional_customer_text(new_company_name)
        )
        normalized_is_active = None if new_is_active is None else bool(normalize_is_active(new_is_active))
    except ValueError as e:
        raise _as_validation_error(e) from e

    if (
        (normalized_name is None or normalized_name == customer.name) and 
        (normalized_email is None or normalized_email == customer.email) and
        (normalized_phone is None or normalized_phone == customer.phone) and
        (normalized_type is None or normalized_type == customer.customer_type) and
        (normalized_company is None or normalized_company == customer.company_name) and
        (normalized_is_active is None or normalized_is_active == customer.is_active)
    ):
        raise exceptions.ValidationError("No changes detected.")
    
    return normalized_name, normalized_email, normalized_phone, normalized_type, normalized_company, normalized_is_active

def _update_customer(
    cursor, 
    customer: customers_db.Customer, 
    new_name: str | None = None, 
    new_email: str | None = None,
    new_phone: str | None = None,
    new_customer_type: str | None = None,
    new_company_name: str | None = None,
    new_is_active: bool | None = None,
) -> customers_db.Customer:
    normalized_name, normalized_email, normalized_phone, normalized_type, normalized_company, normalized_is_active = _prepare_customer_changes(
        customer,
        new_name,
        new_email,
        new_phone,
        new_customer_type,
        new_company_name,
        new_is_active,
    )

    try:
        updated_customer = customers_db.update_customer(
            cursor,
            customer.id,
            name=normalized_name,
            email=normalized_email,
            phone=normalized_phone,
            customer_type=normalized_type,
            company_name=normalized_company,
            is_active=normalized_is_active,
        )
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError(
            f"Customer email already exists ({normalized_email})"
        ) from e 

    if updated_customer is None:
        raise exceptions.ServiceError(f"Failed to update customer {customer.id}.")
    
    return updated_customer

def _normalize_customer_name(customer_name: str) -> str:
    try:
        return normalize_name(customer_name)
    except ValueError as e:
        raise _as_validation_error(e) from e

def _normalize_customer_email(customer_email: str) -> str:
    if customer_email.strip() == "":
        raise exceptions.ValidationError("Customer email cannot be empty.")

    try:
        return normalize_email(customer_email)
    except ValueError as e:
        raise _as_validation_error(e) from e

def _normalize_customer_phone(customer_phone: str | None) -> str | None:
    try:
        return normalize_customer_phone(customer_phone)
    except ValueError as e:
        raise _as_validation_error(e) from e

#CRUD
def create_customer(
    cursor,
    customer_name: str,
    customer_email: str,
    phone: str | None = None,
    customer_type: str = "residential",
    company_name: str | None = None,
    is_active: bool = True,
) -> CustomerRecord:
    customer_name = _normalize_customer_name(customer_name)
    customer_email = _normalize_customer_email(customer_email)
    phone = _normalize_customer_phone(phone)

    try:
        customer_id = customers_db.create_customer(
            cursor,
            customer_name,
            customer_email,
            phone=phone,
            customer_type=customer_type,
            company_name=company_name,
            is_active=is_active,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
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
    new_phone: str | None = None,
    new_customer_type: str | None = None,
    new_company_name: str | None = None,
    new_is_active: bool | None = None,
    ) -> CustomerRecord: 
    customer = _require_customer_by_id(cursor, customer_id)
    return _to_customer_record(_update_customer(
        cursor,
        customer,
        new_name,
        new_email,
        new_phone,
        new_customer_type,
        new_company_name,
        new_is_active,
    ))

def update_customer_by_email(
    cursor,
    customer_email: str,
    new_name: str | None = None,
    new_email: str | None = None,
    new_phone: str | None = None,
    new_customer_type: str | None = None,
    new_company_name: str | None = None,
    new_is_active: bool | None = None,
    ) -> CustomerRecord: 
    customer = _require_customer_by_email(cursor, customer_email)
    updated_customer = _update_customer(
        cursor,
        customer,
        new_name,
        new_email,
        new_phone,
        new_customer_type,
        new_company_name,
        new_is_active,
    )
    return _to_customer_record(updated_customer)

def delete_customer_by_id(cursor, customer_id: int) -> None:
    try:
        validate_positive_id(customer_id, "Customer id")
    except ValueError as e:
        raise _as_validation_error(e) from e
    deleted_customer = customers_db.delete_customer(cursor, customer_id=customer_id)
    
    if not deleted_customer:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")
