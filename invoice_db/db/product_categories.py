from dataclasses import dataclass
from sqlite3 import Row

from .validators import normalize_category_name, normalize_description, normalize_is_active


DEFAULT_CATEGORY_ID = 1
DEFAULT_CATEGORY_NAME = "Uncategorized"


@dataclass
class ProductCategoryCreate:
    name: str
    description: str | None = None
    is_active: bool = True
    workspace_id: int | None = None


@dataclass
class ProductCategory:
    id: int
    workspace_id: int | None
    name: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


def _to_category(row: Row) -> ProductCategory:
    return ProductCategory(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        description=row["description"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_product_category(cursor, category: ProductCategoryCreate) -> ProductCategory:
    name = normalize_category_name(category.name)
    description = normalize_description(category.description)
    is_active = normalize_is_active(category.is_active)

    cursor.execute(
        """
        INSERT INTO product_categories (workspace_id, name, description, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (category.workspace_id, name, description, is_active),
    )

    created_category = get_product_category_by_id(
        cursor,
        cursor.lastrowid,
        workspace_id=category.workspace_id,
    )
    if created_category is None:
        raise RuntimeError("Product category was created but could not be retrieved.")

    return created_category


def get_product_category_by_id(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> ProductCategory | None:
    if workspace_id is None:
        cursor.execute(
            "SELECT * FROM product_categories WHERE id = ? AND workspace_id IS NULL",
            (category_id,),
        )
    else:
        cursor.execute(
            "SELECT * FROM product_categories WHERE id = ? AND workspace_id = ?",
            (category_id, workspace_id),
        )
    row = cursor.fetchone()
    return _to_category(row) if row else None


def get_product_category_by_name(
    cursor,
    name: str,
    workspace_id: int | None = None,
) -> ProductCategory | None:
    normalized_name = normalize_category_name(name)
    if workspace_id is None:
        cursor.execute(
            "SELECT * FROM product_categories WHERE lower(name) = lower(?) AND workspace_id IS NULL",
            (normalized_name,),
        )
    else:
        cursor.execute(
            "SELECT * FROM product_categories WHERE lower(name) = lower(?) AND workspace_id = ?",
            (normalized_name, workspace_id),
        )
    row = cursor.fetchone()
    return _to_category(row) if row else None


def get_product_categories(
    cursor,
    active_only: bool = False,
    workspace_id: int | None = None,
) -> list[ProductCategory]:
    sql = "SELECT * FROM product_categories"
    params = []
    clauses = ["workspace_id IS NULL"] if workspace_id is None else ["workspace_id = ?"]
    if workspace_id is not None:
        params.append(workspace_id)

    if active_only:
        clauses.append("is_active = ?")
        params.append(1)

    sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY name"
    cursor.execute(sql, params)
    return [_to_category(row) for row in cursor.fetchall()]


def get_or_create_default_category(
    cursor,
    workspace_id: int | None = None,
) -> ProductCategory:
    existing = get_product_category_by_name(
        cursor,
        DEFAULT_CATEGORY_NAME,
        workspace_id=workspace_id,
    )
    if existing is not None:
        return existing

    return create_product_category(
        cursor,
        ProductCategoryCreate(
            name=DEFAULT_CATEGORY_NAME,
            description="Default category for uncategorized products.",
            is_active=True,
            workspace_id=workspace_id,
        ),
    )


def update_product_category(
    cursor,
    category_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    workspace_id: int | None = None,
) -> ProductCategory | None:
    updates, params = [], []

    category = get_product_category_by_id(cursor, category_id, workspace_id=workspace_id)
    if category is None:
        return None

    if name is not None:
        updates.append("name = ?")
        params.append(normalize_category_name(name))
    if description is not None:
        updates.append("description = ?")
        params.append(normalize_description(description))
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(normalize_is_active(is_active))

    if not updates:
        return category

    params.append(category_id)
    query = f"UPDATE product_categories SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))

    return get_product_category_by_id(cursor, category_id, workspace_id=workspace_id)


def count_products_for_category(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> int:
    workspace_clause = " AND workspace_id IS NULL" if workspace_id is None else " AND workspace_id = ?"
    params = [category_id] if workspace_id is None else [category_id, workspace_id]
    cursor.execute(
        f"SELECT COUNT(*) AS product_count FROM products WHERE category_id = ?{workspace_clause}",
        params,
    )
    row = cursor.fetchone()
    return row["product_count"] if row else 0


def get_products_for_category(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> list[Row]:
    workspace_clause = " AND products.workspace_id IS NULL" if workspace_id is None else " AND products.workspace_id = ?"
    params = [category_id] if workspace_id is None else [category_id, workspace_id]
    cursor.execute(
        f"""
        SELECT
            products.*,
            product_categories.name AS category_name,
            (
                SELECT COUNT(*)
                FROM product_suppliers
                WHERE product_suppliers.product_id = products.id
            ) AS product_supplier_count,
            (
                SELECT COUNT(*)
                FROM invoice_items
                WHERE invoice_items.product_id = products.id
            ) AS invoice_item_count
        FROM products
        JOIN product_categories ON product_categories.id = products.category_id
        WHERE products.category_id = ?{workspace_clause}
        ORDER BY products.name
        """,
        params,
    )
    return cursor.fetchall()


def get_invoice_totals_for_category(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> list[Row]:
    workspace_clause = " AND i.workspace_id IS NULL" if workspace_id is None else " AND i.workspace_id = ?"
    params = [category_id] if workspace_id is None else [category_id, workspace_id]
    cursor.execute(
        f"""
        SELECT
            i.id,
            i.invoice_number,
            i.customer_id,
            c.name AS customer_name,
            i.date_issued,
            i.date_due,
            i.status,
            COALESCE(SUM(ii.quantity * ii.unit_price), 0) AS revenue_total_cents,
            COALESCE(SUM(ii.quantity * ii.unit_cost), 0) AS cost_total_cents,
            COALESCE(SUM((ii.quantity * ii.unit_price) - (ii.quantity * ii.unit_cost)), 0) AS profit_total_cents
        FROM invoice_items ii
        JOIN products p ON p.id = ii.product_id
        JOIN invoices i ON i.id = ii.invoice_id
        JOIN customers c ON c.id = i.customer_id
        WHERE p.category_id = ?{workspace_clause}
        GROUP BY i.id, i.invoice_number, i.customer_id, c.name, i.date_issued, i.date_due, i.status
        ORDER BY COALESCE(i.date_issued, '') DESC, i.id DESC
        """,
        params,
    )
    return cursor.fetchall()


def delete_product_category(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> bool:
    if workspace_id is None:
        cursor.execute(
            "DELETE FROM product_categories WHERE id = ? AND workspace_id IS NULL",
            (category_id,),
        )
    else:
        cursor.execute(
            "DELETE FROM product_categories WHERE id = ? AND workspace_id = ?",
            (category_id, workspace_id),
        )
    return cursor.rowcount > 0


def assert_product_category_exists(
    cursor,
    category_id: int,
    workspace_id: int | None = None,
) -> None:
    if get_product_category_by_id(cursor, category_id, workspace_id=workspace_id) is None:
        raise ValueError(f"Product category not found (id={category_id})")
