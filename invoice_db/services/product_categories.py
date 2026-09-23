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


class CategoryProductRecord(TypedDict):
    id: int
    name: str
    description: str | None
    cost_cents: int
    unit_price_cents: int
    category_id: int
    category_name: str
    is_active: bool
    product_supplier_count: int
    invoice_item_count: int
    created_at: str
    updated_at: str


class CategoryInvoiceRecord(TypedDict):
    id: int
    customer_id: int
    customer_name: str
    date_issued: str | None
    date_due: str | None
    status: str
    revenue_total_cents: int
    cost_total_cents: int
    profit_total_cents: int


class ProductCategoryMetricsRecord(TypedDict):
    product_count: int
    active_product_count: int
    invoice_count: int
    revenue_total_cents: int
    cost_total_cents: int
    profit_total_cents: int


class ProductCategoryDetailRecord(TypedDict):
    category: ProductCategoryRecord
    metrics: ProductCategoryMetricsRecord
    products: list[CategoryProductRecord]
    invoices: list[CategoryInvoiceRecord]


def _to_category_record(category: categories_db.ProductCategory) -> ProductCategoryRecord:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


def _to_category_product_record(row) -> CategoryProductRecord:
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "cost_cents": row["cost"],
        "unit_price_cents": row["unit_price"],
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "is_active": bool(row["is_active"]),
        "product_supplier_count": row["product_supplier_count"],
        "invoice_item_count": row["invoice_item_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
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


def get_product_category_detail(cursor, category_id: int) -> ProductCategoryDetailRecord:
    category = _require_category(cursor, category_id)
    products = [
        _to_category_product_record(row)
        for row in categories_db.get_products_for_category(cursor, category_id)
    ]
    invoices = [dict(row) for row in categories_db.get_invoice_totals_for_category(cursor, category_id)]
    issued_invoices = [
        invoice for invoice in invoices
        if invoice["status"] in {"sent", "paid"}
    ]

    return {
        "category": _to_category_record(category),
        "metrics": {
            "product_count": len(products),
            "active_product_count": sum(1 for product in products if product["is_active"]),
            "invoice_count": len(invoices),
            "revenue_total_cents": sum(invoice["revenue_total_cents"] for invoice in issued_invoices),
            "cost_total_cents": sum(invoice["cost_total_cents"] for invoice in issued_invoices),
            "profit_total_cents": sum(invoice["profit_total_cents"] for invoice in issued_invoices),
        },
        "products": products,
        "invoices": invoices,
    }


def update_product_category_by_id(
    cursor,
    category_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> ProductCategoryRecord:
    category = _require_category(cursor, category_id)

    if category.id == categories_db.DEFAULT_CATEGORY_ID:
        raise exceptions.ValidationError("The default product category cannot be edited.")

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
    if category.id == categories_db.DEFAULT_CATEGORY_ID:
        raise exceptions.ValidationError("The default product category cannot be deactivated.")

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
