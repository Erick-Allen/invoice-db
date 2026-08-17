from dataclasses import dataclass
from sqlite3 import Row

from . import products as products_db
from .validators import normalize_description, normalize_is_active, normalize_supplier_name


@dataclass
class SupplierCreate:
    name: str
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    is_active: bool = True


@dataclass
class Supplier:
    id: int
    name: str
    phone: str | None
    email: str | None
    website: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class ProductSupplier:
    product_id: int
    supplier_id: int
    note: str | None
    created_at: str
    updated_at: str


def _to_supplier(row: Row) -> Supplier:
    return Supplier(
        id=row["id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        website=row["website"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_product_supplier(row: Row) -> ProductSupplier:
    return ProductSupplier(
        product_id=row["product_id"],
        supplier_id=row["supplier_id"],
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_supplier(cursor, supplier: SupplierCreate) -> Supplier:
    name = normalize_supplier_name(supplier.name)
    phone = normalize_description(supplier.phone)
    email = normalize_description(supplier.email)
    website = normalize_description(supplier.website)
    is_active = normalize_is_active(supplier.is_active)

    cursor.execute(
        """
        INSERT INTO suppliers (name, phone, email, website, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, phone, email, website, is_active),
    )

    created_supplier = get_supplier_by_id(cursor, cursor.lastrowid)
    if created_supplier is None:
        raise RuntimeError("Supplier was created but could not be retrieved.")

    return created_supplier


def get_supplier_by_id(cursor, supplier_id: int) -> Supplier | None:
    cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    row = cursor.fetchone()
    return _to_supplier(row) if row else None


def get_supplier_by_name(cursor, name: str) -> Supplier | None:
    normalized_name = normalize_supplier_name(name)
    cursor.execute(
        "SELECT * FROM suppliers WHERE lower(name) = lower(?)",
        (normalized_name,),
    )
    row = cursor.fetchone()
    return _to_supplier(row) if row else None


def get_suppliers(cursor, active_only: bool = False) -> list[Supplier]:
    sql = "SELECT * FROM suppliers"
    params = []

    if active_only:
        sql += " WHERE is_active = ?"
        params.append(1)

    sql += " ORDER BY name"
    cursor.execute(sql, params)
    return [_to_supplier(row) for row in cursor.fetchall()]


def update_supplier(
    cursor,
    supplier_id: int,
    *,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    website: str | None = None,
    is_active: bool | None = None,
) -> Supplier | None:
    updates, params = [], []

    supplier = get_supplier_by_id(cursor, supplier_id)
    if supplier is None:
        return None

    if name is not None:
        updates.append("name = ?")
        params.append(normalize_supplier_name(name))
    if phone is not None:
        updates.append("phone = ?")
        params.append(normalize_description(phone))
    if email is not None:
        updates.append("email = ?")
        params.append(normalize_description(email))
    if website is not None:
        updates.append("website = ?")
        params.append(normalize_description(website))
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(normalize_is_active(is_active))

    if not updates:
        return supplier

    params.append(supplier_id)
    query = f"UPDATE suppliers SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))

    return get_supplier_by_id(cursor, supplier_id)


def delete_supplier(cursor, supplier_id: int) -> bool:
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    return cursor.rowcount > 0


def count_products_for_supplier(cursor, supplier_id: int) -> int:
    cursor.execute(
        "SELECT COUNT(*) AS product_count FROM product_suppliers WHERE supplier_id = ?",
        (supplier_id,),
    )
    row = cursor.fetchone()
    return row["product_count"] if row else 0


def add_supplier_to_product(
    cursor,
    product_id: int,
    supplier_id: int,
    note: str | None = None,
) -> ProductSupplier:
    cursor.execute(
        """
        INSERT INTO product_suppliers (product_id, supplier_id, note)
        VALUES (?, ?, ?)
        """,
        (product_id, supplier_id, normalize_description(note)),
    )

    product_supplier = get_product_supplier(cursor, product_id, supplier_id)
    if product_supplier is None:
        raise RuntimeError("Product supplier was created but could not be retrieved.")

    return product_supplier


def get_product_supplier(cursor, product_id: int, supplier_id: int) -> ProductSupplier | None:
    cursor.execute(
        """
        SELECT *
        FROM product_suppliers
        WHERE product_id = ? AND supplier_id = ?
        """,
        (product_id, supplier_id),
    )
    row = cursor.fetchone()
    return _to_product_supplier(row) if row else None


def get_suppliers_for_product(cursor, product_id: int) -> list[Supplier]:
    cursor.execute(
        """
        SELECT suppliers.*
        FROM suppliers
        JOIN product_suppliers ON product_suppliers.supplier_id = suppliers.id
        WHERE product_suppliers.product_id = ?
        ORDER BY suppliers.name
        """,
        (product_id,),
    )
    return [_to_supplier(row) for row in cursor.fetchall()]


def get_products_for_supplier(cursor, supplier_id: int) -> list[products_db.Product]:
    cursor.execute(
        """
        SELECT products.*, product_categories.name AS category_name
        FROM products
        JOIN product_categories ON product_categories.id = products.category_id
        JOIN product_suppliers ON product_suppliers.product_id = products.id
        WHERE product_suppliers.supplier_id = ?
        ORDER BY products.name
        """,
        (supplier_id,),
    )
    return [products_db._to_product(row) for row in cursor.fetchall()]


def update_product_supplier_note(
    cursor,
    product_id: int,
    supplier_id: int,
    note: str | None,
) -> ProductSupplier | None:
    product_supplier = get_product_supplier(cursor, product_id, supplier_id)
    if product_supplier is None:
        return None

    cursor.execute(
        """
        UPDATE product_suppliers
        SET note = ?
        WHERE product_id = ? AND supplier_id = ?
        """,
        (normalize_description(note), product_id, supplier_id),
    )
    return get_product_supplier(cursor, product_id, supplier_id)


def remove_supplier_from_product(cursor, product_id: int, supplier_id: int) -> bool:
    cursor.execute(
        """
        DELETE FROM product_suppliers
        WHERE product_id = ? AND supplier_id = ?
        """,
        (product_id, supplier_id),
    )
    return cursor.rowcount > 0


def remove_supplier_from_all_products(cursor, supplier_id: int) -> int:
    cursor.execute(
        "DELETE FROM product_suppliers WHERE supplier_id = ?",
        (supplier_id,),
    )
    return cursor.rowcount
