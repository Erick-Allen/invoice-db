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


@dataclass
class ProductCategory:
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


def _to_category(row: Row) -> ProductCategory:
    return ProductCategory(
        id=row["id"],
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
        INSERT INTO product_categories (name, description, is_active)
        VALUES (?, ?, ?)
        """,
        (name, description, is_active),
    )

    created_category = get_product_category_by_id(cursor, cursor.lastrowid)
    if created_category is None:
        raise RuntimeError("Product category was created but could not be retrieved.")

    return created_category


def get_product_category_by_id(cursor, category_id: int) -> ProductCategory | None:
    cursor.execute("SELECT * FROM product_categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    return _to_category(row) if row else None


def get_product_category_by_name(cursor, name: str) -> ProductCategory | None:
    normalized_name = normalize_category_name(name)
    cursor.execute(
        "SELECT * FROM product_categories WHERE lower(name) = lower(?)",
        (normalized_name,),
    )
    row = cursor.fetchone()
    return _to_category(row) if row else None


def get_product_categories(cursor, active_only: bool = False) -> list[ProductCategory]:
    sql = "SELECT * FROM product_categories"
    params = []

    if active_only:
        sql += " WHERE is_active = ?"
        params.append(1)

    sql += " ORDER BY name"
    cursor.execute(sql, params)
    return [_to_category(row) for row in cursor.fetchall()]


def update_product_category(
    cursor,
    category_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> ProductCategory | None:
    updates, params = [], []

    category = get_product_category_by_id(cursor, category_id)
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

    return get_product_category_by_id(cursor, category_id)


def assert_product_category_exists(cursor, category_id: int) -> None:
    if get_product_category_by_id(cursor, category_id) is None:
        raise ValueError(f"Product category not found (id={category_id})")
