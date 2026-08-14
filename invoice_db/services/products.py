import sqlite3
from typing import TypedDict

from invoice_db.db import products as products_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


class ProductRecord(TypedDict):
    id: int
    name: str
    description: str | None
    unit_price_cents: int
    category_id: int
    category_name: str
    is_active: bool
    created_at: str
    updated_at: str


def _to_product_record(product: products_db.Product) -> ProductRecord:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "unit_price_cents": product.unit_price_cents,
        "category_id": product.category_id,
        "category_name": product.category_name,
        "is_active": product.is_active,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _require_product(cursor, product_id: int) -> products_db.Product:
    try:
        validate_positive_id(product_id, "Product id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    product = products_db.get_product_by_id(cursor, product_id)
    if product is None:
        raise exceptions.NotFoundError(f"Product not found (id={product_id})")

    return product


def create_product(
    cursor,
    name: str,
    unit_price_cents: int,
    description: str | None = None,
    category_id: int = 1,
    is_active: bool = True,
) -> ProductRecord:
    try:
        product = products_db.create_product(
            cursor,
            products_db.ProductCreate(
                name=name,
                description=description,
                unit_price_cents=unit_price_cents,
                category_id=category_id,
                is_active=is_active,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid product data.") from e

    return _to_product_record(product)


def list_products(cursor, active_only: bool = False) -> list[ProductRecord]:
    return [_to_product_record(product) for product in products_db.get_products(cursor, active_only=active_only)]


def get_product_by_id(cursor, product_id: int) -> ProductRecord:
    return _to_product_record(_require_product(cursor, product_id))


def update_product_by_id(
    cursor,
    product_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    unit_price_cents: int | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
) -> ProductRecord:
    product = _require_product(cursor, product_id)

    if name is None and description is None and unit_price_cents is None and category_id is None and is_active is None:
        raise exceptions.ValidationError("Please provide at least one value to update the product.")

    try:
        updated_product = products_db.update_product(
            cursor,
            product_id=product.id,
            name=name,
            description=description,
            unit_price_cents=unit_price_cents,
            category_id=category_id,
            is_active=is_active,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid product update data.") from e

    if updated_product is None:
        raise exceptions.ServiceError(f"Failed to update product {product_id}.")

    return _to_product_record(updated_product)


def deactivate_product(cursor, product_id: int) -> ProductRecord:
    product = _require_product(cursor, product_id)
    if not product.is_active:
        raise exceptions.ValidationError("Product is already inactive.")

    return update_product_by_id(cursor, product_id, is_active=False)


def delete_product(cursor, product_id: int) -> None:
    _require_product(cursor, product_id)
    deleted = products_db.delete_product(cursor, product_id)

    if not deleted:
        raise exceptions.NotFoundError(f"Product not found (id={product_id})")
