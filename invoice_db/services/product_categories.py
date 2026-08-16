import sqlite3
from typing import TypedDict

from invoice_db.db import product_categories as categories_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


class ProductCategoryRecord(TypedDict):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


def _to_category_record(category: categories_db.ProductCategory) -> ProductCategoryRecord:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _require_category(cursor, category_id: int) -> categories_db.ProductCategory:
    try:
        validate_positive_id(category_id, "Product category id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    category = categories_db.get_product_category_by_id(cursor, category_id)
    if category is None:
        raise exceptions.NotFoundError(f"Product category not found (id={category_id})")

    return category


def _raise_if_category_name_exists(
    cursor,
    name: str,
    *,
    current_category_id: int | None = None,
) -> None:
    existing_category = categories_db.get_product_category_by_name(cursor, name)
    if existing_category is not None and existing_category.id != current_category_id:
        raise exceptions.ValidationError(
            f'A product category named "{existing_category.name}" already exists.'
        )


def create_product_category(
    cursor,
    name: str,
    description: str | None = None,
    is_active: bool = True,
) -> ProductCategoryRecord:
    try:
        _raise_if_category_name_exists(cursor, name)
        category = categories_db.create_product_category(
            cursor,
            categories_db.ProductCategoryCreate(
                name=name,
                description=description,
                is_active=is_active,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid product category data.") from e

    return _to_category_record(category)


def list_product_categories(cursor, active_only: bool = False) -> list[ProductCategoryRecord]:
    return [
        _to_category_record(category)
        for category in categories_db.get_product_categories(cursor, active_only=active_only)
    ]


def update_product_category_by_id(
    cursor,
    category_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> ProductCategoryRecord:
    _require_category(cursor, category_id)

    if name is None and description is None and is_active is None:
        raise exceptions.ValidationError("Please provide at least one value to update the product category.")

    try:
        if name is not None:
            _raise_if_category_name_exists(cursor, name, current_category_id=category_id)

        updated_category = categories_db.update_product_category(
            cursor,
            category_id=category_id,
            name=name,
            description=description,
            is_active=is_active,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid product category update data.") from e

    if updated_category is None:
        raise exceptions.ServiceError(f"Failed to update product category {category_id}.")

    return _to_category_record(updated_category)


def deactivate_product_category(cursor, category_id: int) -> ProductCategoryRecord:
    category = _require_category(cursor, category_id)
    if not category.is_active:
        raise exceptions.ValidationError("Product category is already inactive.")

    return update_product_category_by_id(cursor, category_id, is_active=False)


def delete_product_category(cursor, category_id: int) -> None:
    category = _require_category(cursor, category_id)

    if category.id == categories_db.DEFAULT_CATEGORY_ID:
        raise exceptions.ValidationError("The default product category cannot be deleted.")

    product_count = categories_db.count_products_for_category(cursor, category_id)
    if product_count > 0:
        product_word = "product" if product_count == 1 else "products"
        verb = "uses" if product_count == 1 else "use"
        raise exceptions.ConflictError(
            f'Cannot delete product category "{category.name}" because {product_count} {product_word} {verb} it.'
        )

    deleted = categories_db.delete_product_category(cursor, category_id)
    if not deleted:
        raise exceptions.NotFoundError(f"Product category not found (id={category_id})")
