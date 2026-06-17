from dataclasses import dataclass
from sqlite3 import Row

from .validators import (
    normalize_description,
    normalize_is_active,
    normalize_product_name,
    validate_unit_price_cents,
)

@dataclass
class ProductCreate:
    name: str
    unit_price_cents: int
    description: str | None = None
    is_active: bool = True

@dataclass
class Product:
    id: int
    name: str
    description: str | None
    unit_price_cents: int
    is_active: bool
    created_at: str
    updated_at: str


def _to_product(row: Row) -> Product:
    return Product(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        unit_price_cents=row["unit_price"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_product(cursor, product: ProductCreate) -> Product:
    name = normalize_product_name(product.name)
    description = normalize_description(product.description)
    unit_price_cents = validate_unit_price_cents(product.unit_price_cents)
    is_active = normalize_is_active(product.is_active)

    cursor.execute("""
        INSERT INTO products (name, description, unit_price, is_active)
        VALUES (?, ?, ?, ?)
    """, (name, description, unit_price_cents, is_active))

    created_product = get_product_by_id(cursor, cursor.lastrowid)

    if created_product is None:
        raise RuntimeError("Product was created but could not be retrieved.")
    
    return created_product


def get_product_by_id(cursor, product_id: int) -> Product | None:
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    return _to_product(row) if row else None


def get_products(cursor, active_only: bool = False) -> list[Product]:
    sql = "SELECT * FROM products"
    params = []

    if active_only:
        sql += " WHERE is_active = ?"
        params.append(1)

    sql += " ORDER BY id"
    cursor.execute(sql, params)
    return [_to_product(row) for row in cursor.fetchall()]


def update_product(
    cursor,
    product_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    unit_price_cents: int | None = None,
    is_active: bool | None = None,
) -> Product | None:
    updates, params = [], []

    product = get_product_by_id(cursor, product_id)
    if product is None:
        return None

    if name is not None:
        updates.append("name = ?")
        params.append(normalize_product_name(name))
    if description is not None:
        updates.append("description = ?")
        params.append(normalize_description(description))
    if unit_price_cents is not None:
        updates.append("unit_price = ?")
        params.append(validate_unit_price_cents(unit_price_cents))
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(normalize_is_active(is_active))

    if not updates:
        return product

    params.append(product_id)
    query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))

    return get_product_by_id(cursor, product_id)


def delete_product(cursor, product_id: int) -> bool:
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    return cursor.rowcount > 0


def assert_product_exists(cursor, product_id: int) -> None:
    if get_product_by_id(cursor, product_id) is None:
        raise ValueError(f"Product not found (id={product_id})")
