import sqlite3
from typing import TypedDict

from invoice_db.db import products as products_db
from invoice_db.db import suppliers as suppliers_db
from invoice_db.db.validators import validate_positive_id

from . import exceptions


class SupplierRecord(TypedDict):
    id: int
    name: str
    phone: str | None
    email: str | None
    website: str | None
    is_active: bool
    created_at: str
    updated_at: str


class ProductSupplierRecord(TypedDict):
    product_id: int
    supplier_id: int
    note: str | None
    created_at: str
    updated_at: str


def _to_supplier_record(supplier: suppliers_db.Supplier) -> SupplierRecord:
    return {
        "id": supplier.id,
        "name": supplier.name,
        "phone": supplier.phone,
        "email": supplier.email,
        "website": supplier.website,
        "is_active": supplier.is_active,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at,
    }


def _to_product_supplier_record(product_supplier: suppliers_db.ProductSupplier) -> ProductSupplierRecord:
    return {
        "product_id": product_supplier.product_id,
        "supplier_id": product_supplier.supplier_id,
        "note": product_supplier.note,
        "created_at": product_supplier.created_at,
        "updated_at": product_supplier.updated_at,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _validate_id(value: int, label: str) -> None:
    try:
        validate_positive_id(value, label)
    except ValueError as e:
        raise _as_validation_error(e) from e


def _require_product(cursor, product_id: int) -> products_db.Product:
    _validate_id(product_id, "Product id")
    product = products_db.get_product_by_id(cursor, product_id)
    if product is None:
        raise exceptions.NotFoundError(f"Product not found (id={product_id})")
    return product


def _require_supplier(cursor, supplier_id: int) -> suppliers_db.Supplier:
    _validate_id(supplier_id, "Supplier id")
    supplier = suppliers_db.get_supplier_by_id(cursor, supplier_id)
    if supplier is None:
        raise exceptions.NotFoundError(f"Supplier not found (id={supplier_id})")
    return supplier


def _raise_if_supplier_name_exists(
    cursor,
    name: str,
    *,
    current_supplier_id: int | None = None,
) -> None:
    existing_supplier = suppliers_db.get_supplier_by_name(cursor, name)
    if existing_supplier is not None and existing_supplier.id != current_supplier_id:
        raise exceptions.ValidationError(
            f'A supplier named "{existing_supplier.name}" already exists.'
        )


def create_supplier(
    cursor,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    website: str | None = None,
    is_active: bool = True,
) -> SupplierRecord:
    try:
        _raise_if_supplier_name_exists(cursor, name)
        supplier = suppliers_db.create_supplier(
            cursor,
            suppliers_db.SupplierCreate(
                name=name,
                phone=phone,
                email=email,
                website=website,
                is_active=is_active,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid supplier data.") from e

    return _to_supplier_record(supplier)


def list_suppliers(cursor, active_only: bool = False) -> list[SupplierRecord]:
    return [
        _to_supplier_record(supplier)
        for supplier in suppliers_db.get_suppliers(cursor, active_only=active_only)
    ]


def get_supplier_by_id(cursor, supplier_id: int) -> SupplierRecord:
    return _to_supplier_record(_require_supplier(cursor, supplier_id))


def update_supplier_by_id(
    cursor,
    supplier_id: int,
    *,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    website: str | None = None,
    is_active: bool | None = None,
) -> SupplierRecord:
    _require_supplier(cursor, supplier_id)

    if name is None and phone is None and email is None and website is None and is_active is None:
        raise exceptions.ValidationError("Please provide at least one value to update the supplier.")

    try:
        if name is not None:
            _raise_if_supplier_name_exists(cursor, name, current_supplier_id=supplier_id)

        updated_supplier = suppliers_db.update_supplier(
            cursor,
            supplier_id=supplier_id,
            name=name,
            phone=phone,
            email=email,
            website=website,
            is_active=is_active,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid supplier update data.") from e

    if updated_supplier is None:
        raise exceptions.ServiceError(f"Failed to update supplier {supplier_id}.")

    return _to_supplier_record(updated_supplier)


def deactivate_supplier(cursor, supplier_id: int) -> SupplierRecord:
    supplier = _require_supplier(cursor, supplier_id)
    if not supplier.is_active:
        raise exceptions.ValidationError("Supplier is already inactive.")

    return update_supplier_by_id(cursor, supplier_id, is_active=False)


def delete_supplier(cursor, supplier_id: int) -> None:
    supplier = _require_supplier(cursor, supplier_id)
    product_count = suppliers_db.count_products_for_supplier(cursor, supplier_id)

    if product_count > 0:
        product_word = "product" if product_count == 1 else "products"
        verb = "uses" if product_count == 1 else "use"
        raise exceptions.ConflictError(
            f'Cannot delete supplier "{supplier.name}" because {product_count} {product_word} {verb} it.'
        )

    deleted = suppliers_db.delete_supplier(cursor, supplier_id)
    if not deleted:
        raise exceptions.NotFoundError(f"Supplier not found (id={supplier_id})")


def add_supplier_to_product(
    cursor,
    product_id: int,
    supplier_id: int,
    note: str | None = None,
) -> ProductSupplierRecord:
    _require_product(cursor, product_id)
    supplier = _require_supplier(cursor, supplier_id)

    if not supplier.is_active:
        raise exceptions.ValidationError("Inactive suppliers cannot be added to products.")

    try:
        product_supplier = suppliers_db.add_supplier_to_product(
            cursor,
            product_id,
            supplier_id,
            note,
        )
    except sqlite3.IntegrityError as e:
        if suppliers_db.get_product_supplier(cursor, product_id, supplier_id) is not None:
            raise exceptions.ConflictError(
                f'Supplier "{supplier.name}" is already attached to product {product_id}.'
            ) from e
        raise exceptions.ValidationError("Invalid product supplier data.") from e

    return _to_product_supplier_record(product_supplier)


def list_product_suppliers(cursor, product_id: int) -> list[SupplierRecord]:
    _require_product(cursor, product_id)
    return [
        _to_supplier_record(supplier)
        for supplier in suppliers_db.get_suppliers_for_product(cursor, product_id)
    ]


def list_supplier_products(cursor, supplier_id: int) -> list[dict]:
    _require_supplier(cursor, supplier_id)
    return [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "cost_cents": product.cost_cents,
            "unit_price_cents": product.unit_price_cents,
            "category_id": product.category_id,
            "category_name": product.category_name,
            "is_active": product.is_active,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }
        for product in suppliers_db.get_products_for_supplier(cursor, supplier_id)
    ]


def update_product_supplier_note(
    cursor,
    product_id: int,
    supplier_id: int,
    note: str | None,
) -> ProductSupplierRecord:
    _require_product(cursor, product_id)
    _require_supplier(cursor, supplier_id)

    updated = suppliers_db.update_product_supplier_note(cursor, product_id, supplier_id, note)
    if updated is None:
        raise exceptions.NotFoundError(
            f"Supplier not attached to product (product_id={product_id}, supplier_id={supplier_id})"
        )

    return _to_product_supplier_record(updated)


def remove_supplier_from_product(cursor, product_id: int, supplier_id: int) -> None:
    _require_product(cursor, product_id)
    _require_supplier(cursor, supplier_id)

    removed = suppliers_db.remove_supplier_from_product(cursor, product_id, supplier_id)
    if not removed:
        raise exceptions.NotFoundError(
            f"Supplier not attached to product (product_id={product_id}, supplier_id={supplier_id})"
        )


def remove_supplier_from_all_products(cursor, supplier_id: int) -> dict:
    supplier = _require_supplier(cursor, supplier_id)
    if supplier.is_active:
        raise exceptions.ValidationError("Only inactive suppliers can be removed from all products.")

    removed_count = suppliers_db.remove_supplier_from_all_products(cursor, supplier_id)
    return {
        "supplier_id": supplier_id,
        "removed_count": removed_count,
    }
