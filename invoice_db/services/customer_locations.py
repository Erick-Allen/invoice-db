import sqlite3
from typing import TypedDict

from invoice_db.db import customer_locations as locations_db
from invoice_db.db import customers as customers_db
from invoice_db.db import suppliers as suppliers_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


class CustomerLocationRecord(TypedDict):
    id: int
    customer_id: int
    location_id: int
    label: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


class SupplierLocationRecord(TypedDict):
    id: int
    supplier_id: int
    location_id: int
    label: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


class LocationRecord(TypedDict):
    id: int
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    assigned_customer_count: int
    assigned_customer_names: str | None
    assigned_supplier_count: int
    assigned_supplier_names: str | None
    assigned_count: int
    assigned_names: str | None
    created_at: str
    updated_at: str


class LocationCustomerAssignmentRecord(TypedDict):
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    label: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


class LocationSupplierAssignmentRecord(TypedDict):
    id: int
    supplier_id: int
    supplier_name: str
    supplier_phone: str | None
    supplier_email: str | None
    label: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


class LocationInvoiceRecord(TypedDict):
    id: int
    customer_id: int
    customer_name: str
    customer_location_id: int
    date_issued: str | None
    date_due: str | None
    total: int
    status: str


class LocationDetailRecord(TypedDict):
    location: LocationRecord
    customer_assignments: list[LocationCustomerAssignmentRecord]
    supplier_assignments: list[LocationSupplierAssignmentRecord]
    invoices: list[LocationInvoiceRecord]


def _to_location_record(location: locations_db.CustomerLocation) -> CustomerLocationRecord:
    return {
        "id": location.id,
        "customer_id": location.customer_id,
        "location_id": location.location_id,
        "label": location.label,
        "address_line1": location.address_line1,
        "address_line2": location.address_line2,
        "city": location.city,
        "state": location.state,
        "postal_code": location.postal_code,
        "country": location.country,
        "is_primary": location.is_primary,
        "is_active": location.is_active,
        "notes": location.notes,
        "created_at": location.created_at,
        "updated_at": location.updated_at,
    }


def _to_supplier_location_record(location: locations_db.SupplierLocation) -> SupplierLocationRecord:
    return {
        "id": location.id,
        "supplier_id": location.supplier_id,
        "location_id": location.location_id,
        "label": location.label,
        "address_line1": location.address_line1,
        "address_line2": location.address_line2,
        "city": location.city,
        "state": location.state,
        "postal_code": location.postal_code,
        "country": location.country,
        "is_primary": location.is_primary,
        "is_active": location.is_active,
        "notes": location.notes,
        "created_at": location.created_at,
        "updated_at": location.updated_at,
    }


def _to_global_location_record(location: locations_db.Location) -> LocationRecord:
    return {
        "id": location.id,
        "address_line1": location.address_line1,
        "address_line2": location.address_line2,
        "city": location.city,
        "state": location.state,
        "postal_code": location.postal_code,
        "country": location.country,
        "assigned_customer_count": location.assigned_customer_count,
        "assigned_customer_names": location.assigned_customer_names,
        "assigned_supplier_count": location.assigned_supplier_count,
        "assigned_supplier_names": location.assigned_supplier_names,
        "assigned_count": location.assigned_count,
        "assigned_names": location.assigned_names,
        "created_at": location.created_at,
        "updated_at": location.updated_at,
    }


def _to_location_customer_assignment_record(
    assignment: locations_db.LocationCustomerAssignment,
) -> LocationCustomerAssignmentRecord:
    return {
        "id": assignment.id,
        "customer_id": assignment.customer_id,
        "customer_name": assignment.customer_name,
        "customer_email": assignment.customer_email,
        "label": assignment.label,
        "is_primary": assignment.is_primary,
        "is_active": assignment.is_active,
        "notes": assignment.notes,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }


def _to_location_supplier_assignment_record(
    assignment: locations_db.LocationSupplierAssignment,
) -> LocationSupplierAssignmentRecord:
    return {
        "id": assignment.id,
        "supplier_id": assignment.supplier_id,
        "supplier_name": assignment.supplier_name,
        "supplier_phone": assignment.supplier_phone,
        "supplier_email": assignment.supplier_email,
        "label": assignment.label,
        "is_primary": assignment.is_primary,
        "is_active": assignment.is_active,
        "notes": assignment.notes,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }


def _to_location_invoice_record(invoice: locations_db.LocationInvoice) -> LocationInvoiceRecord:
    return {
        "id": invoice.id,
        "customer_id": invoice.customer_id,
        "customer_name": invoice.customer_name,
        "customer_location_id": invoice.customer_location_id,
        "date_issued": invoice.date_issued,
        "date_due": invoice.date_due,
        "total": invoice.total,
        "status": invoice.status,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _require_customer(cursor, customer_id: int) -> customers_db.Customer:
    try:
        validate_positive_id(customer_id, "Customer id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    customer = customers_db.get_customer_by_id(cursor, customer_id)
    if customer is None:
        raise exceptions.NotFoundError(f"Customer not found (id={customer_id})")

    return customer


def _require_supplier(cursor, supplier_id: int) -> suppliers_db.Supplier:
    try:
        validate_positive_id(supplier_id, "Supplier id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    supplier = suppliers_db.get_supplier_by_id(cursor, supplier_id)
    if supplier is None:
        raise exceptions.NotFoundError(f"Supplier not found (id={supplier_id})")

    return supplier


def _require_location(cursor, location_id: int) -> locations_db.CustomerLocation:
    try:
        validate_positive_id(location_id, "Customer location id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    location = locations_db.get_customer_location_by_id(cursor, location_id)
    if location is None:
        raise exceptions.NotFoundError(f"Customer location not found (id={location_id})")

    return location


def _require_supplier_location_record(cursor, location_id: int) -> locations_db.SupplierLocation:
    try:
        validate_positive_id(location_id, "Supplier location id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    location = locations_db.get_supplier_location_by_id(cursor, location_id)
    if location is None:
        raise exceptions.NotFoundError(f"Supplier location not found (id={location_id})")

    return location


def _require_customer_location(
    cursor,
    customer_id: int,
    location_id: int,
) -> locations_db.CustomerLocation:
    _require_customer(cursor, customer_id)
    location = _require_location(cursor, location_id)

    if location.customer_id != customer_id:
        raise exceptions.ValidationError(
            f"Customer location {location_id} does not belong to customer {customer_id}."
        )

    return location


def _require_supplier_location(
    cursor,
    supplier_id: int,
    location_id: int,
) -> locations_db.SupplierLocation:
    _require_supplier(cursor, supplier_id)
    location = _require_supplier_location_record(cursor, location_id)

    if location.supplier_id != supplier_id:
        raise exceptions.ValidationError(
            f"Supplier location {location_id} does not belong to supplier {supplier_id}."
        )

    return location


def create_customer_location(
    cursor,
    *,
    customer_id: int,
    label: str,
    address_line1: str,
    city: str,
    state: str,
    postal_code: str,
    address_line2: str | None = None,
    country: str = "US",
    is_primary: bool = False,
    is_active: bool = True,
    notes: str | None = None,
) -> CustomerLocationRecord:
    try:
        location = locations_db.create_customer_location(
            cursor,
            locations_db.CustomerLocationCreate(
                customer_id=customer_id,
                label=label,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_primary=is_primary,
                is_active=is_active,
                notes=notes,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid customer location data.") from e

    return _to_location_record(location)


def create_supplier_location(
    cursor,
    *,
    supplier_id: int,
    label: str,
    address_line1: str,
    city: str,
    state: str,
    postal_code: str,
    address_line2: str | None = None,
    country: str = "US",
    is_primary: bool = False,
    is_active: bool = True,
    notes: str | None = None,
) -> SupplierLocationRecord:
    try:
        location = locations_db.create_supplier_location(
            cursor,
            locations_db.SupplierLocationCreate(
                supplier_id=supplier_id,
                label=label,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_primary=is_primary,
                is_active=is_active,
                notes=notes,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid supplier location data.") from e

    return _to_supplier_location_record(location)


def list_locations(cursor) -> list[LocationRecord]:
    return [_to_global_location_record(location) for location in locations_db.get_locations(cursor)]


def create_location(
    cursor,
    *,
    address_line1: str,
    city: str,
    state: str,
    postal_code: str,
    address_line2: str | None = None,
    country: str = "US",
) -> LocationRecord:
    try:
        location = locations_db.create_location(
            cursor,
            locations_db.LocationCreate(
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid location data.") from e

    return _to_global_location_record(location)


def update_location_by_id(
    cursor,
    *,
    location_id: int,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
) -> LocationRecord:
    try:
        validate_positive_id(location_id, "Location id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    if (
        address_line1 is None
        and address_line2 is None
        and city is None
        and state is None
        and postal_code is None
        and country is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the location.")

    try:
        location = locations_db.update_location(
            cursor,
            location_id,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid location update data.") from e

    if location is None:
        raise exceptions.NotFoundError(f"Location not found (id={location_id})")

    return _to_global_location_record(location)


def get_location_detail(cursor, *, location_id: int) -> LocationDetailRecord:
    try:
        validate_positive_id(location_id, "Location id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    location = locations_db.get_location_by_id(cursor, location_id)
    if location is None:
        raise exceptions.NotFoundError(f"Location not found (id={location_id})")

    assignments = locations_db.get_location_customer_assignments(cursor, location_id)
    supplier_assignments = locations_db.get_location_supplier_assignments(cursor, location_id)
    invoices = locations_db.get_location_invoices(cursor, location_id)

    return {
        "location": _to_global_location_record(location),
        "customer_assignments": [
            _to_location_customer_assignment_record(assignment)
            for assignment in assignments
        ],
        "supplier_assignments": [
            _to_location_supplier_assignment_record(assignment)
            for assignment in supplier_assignments
        ],
        "invoices": [_to_location_invoice_record(invoice) for invoice in invoices],
    }


def list_customer_locations(
    cursor,
    *,
    customer_id: int,
    active_only: bool = False,
) -> list[CustomerLocationRecord]:
    _require_customer(cursor, customer_id)
    return [
        _to_location_record(location)
        for location in locations_db.get_customer_locations(cursor, customer_id, active_only=active_only)
    ]


def get_customer_location_by_id(
    cursor,
    *,
    customer_id: int,
    location_id: int,
) -> CustomerLocationRecord:
    return _to_location_record(_require_customer_location(cursor, customer_id, location_id))


def list_supplier_locations(
    cursor,
    *,
    supplier_id: int,
    active_only: bool = False,
) -> list[SupplierLocationRecord]:
    _require_supplier(cursor, supplier_id)
    return [
        _to_supplier_location_record(location)
        for location in locations_db.get_supplier_locations(cursor, supplier_id, active_only=active_only)
    ]


def get_supplier_location_by_id(
    cursor,
    *,
    supplier_id: int,
    location_id: int,
) -> SupplierLocationRecord:
    return _to_supplier_location_record(_require_supplier_location(cursor, supplier_id, location_id))


def update_customer_location_by_id(
    cursor,
    *,
    customer_id: int,
    location_id: int,
    label: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    is_primary: bool | None = None,
    is_active: bool | None = None,
    notes: str | None = None,
) -> CustomerLocationRecord:
    location = _require_customer_location(cursor, customer_id, location_id)

    if (
        label is None
        and address_line1 is None
        and address_line2 is None
        and city is None
        and state is None
        and postal_code is None
        and country is None
        and is_primary is None
        and is_active is None
        and notes is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the customer location.")

    try:
        updated_location = locations_db.update_customer_location(
            cursor,
            location.id,
            label=label,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_primary=is_primary,
            is_active=is_active,
            notes=notes,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid customer location update data.") from e

    if updated_location is None:
        raise exceptions.ServiceError(f"Failed to update customer location {location_id}.")

    return _to_location_record(updated_location)


def update_supplier_location_by_id(
    cursor,
    *,
    supplier_id: int,
    location_id: int,
    label: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    is_primary: bool | None = None,
    is_active: bool | None = None,
    notes: str | None = None,
) -> SupplierLocationRecord:
    location = _require_supplier_location(cursor, supplier_id, location_id)

    if (
        label is None
        and address_line1 is None
        and address_line2 is None
        and city is None
        and state is None
        and postal_code is None
        and country is None
        and is_primary is None
        and is_active is None
        and notes is None
    ):
        raise exceptions.ValidationError("Please provide at least one value to update the supplier location.")

    try:
        updated_location = locations_db.update_supplier_location(
            cursor,
            location.id,
            label=label,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_primary=is_primary,
            is_active=is_active,
            notes=notes,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid supplier location update data.") from e

    if updated_location is None:
        raise exceptions.ServiceError(f"Failed to update supplier location {location_id}.")

    return _to_supplier_location_record(updated_location)


def deactivate_customer_location(
    cursor,
    *,
    customer_id: int,
    location_id: int,
) -> CustomerLocationRecord:
    return update_customer_location_by_id(
        cursor,
        customer_id=customer_id,
        location_id=location_id,
        is_active=False,
        is_primary=False,
    )


def delete_customer_location(
    cursor,
    *,
    customer_id: int,
    location_id: int,
) -> None:
    location = _require_customer_location(cursor, customer_id, location_id)

    try:
        deleted = locations_db.delete_customer_location(cursor, location.id)
    except sqlite3.IntegrityError as e:
        raise exceptions.ConflictError(
            f"Cannot delete customer location {location_id} because it is used by existing invoices."
        ) from e

    if not deleted:
        raise exceptions.NotFoundError(f"Customer location not found (id={location_id})")


def deactivate_supplier_location(
    cursor,
    *,
    supplier_id: int,
    location_id: int,
) -> SupplierLocationRecord:
    return update_supplier_location_by_id(
        cursor,
        supplier_id=supplier_id,
        location_id=location_id,
        is_active=False,
        is_primary=False,
    )


def delete_supplier_location(
    cursor,
    *,
    supplier_id: int,
    location_id: int,
) -> None:
    location = _require_supplier_location(cursor, supplier_id, location_id)

    try:
        deleted = locations_db.delete_supplier_location(cursor, location.id)
    except sqlite3.IntegrityError as e:
        raise exceptions.ConflictError(
            f"Cannot delete supplier location {location_id} because it is used by existing records."
        ) from e

    if not deleted:
        raise exceptions.NotFoundError(f"Supplier location not found (id={location_id})")


def require_location_for_invoice_customer(
    cursor,
    *,
    customer_id: int,
    location_id: int | None,
) -> int | None:
    if location_id is None:
        return None

    _require_customer_location(cursor, customer_id, location_id)
    return location_id
