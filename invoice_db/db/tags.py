from dataclasses import dataclass
from sqlite3 import Row

from .validators import normalize_description, normalize_is_active, normalize_tag_name


@dataclass
class TagCreate:
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass
class Tag:
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class InvoiceTag:
    invoice_id: int
    tag_id: int
    created_at: str


def _to_tag(row: Row) -> Tag:
    return Tag(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_invoice_tag(row: Row) -> InvoiceTag:
    return InvoiceTag(
        invoice_id=row["invoice_id"],
        tag_id=row["tag_id"],
        created_at=row["created_at"],
    )


def create_tag(cursor, tag: TagCreate) -> Tag:
    name = normalize_tag_name(tag.name)
    description = normalize_description(tag.description)
    is_active = normalize_is_active(tag.is_active)

    cursor.execute(
        """
        INSERT INTO tags (name, description, is_active)
        VALUES (?, ?, ?)
        """,
        (name, description, is_active),
    )

    created_tag = get_tag_by_id(cursor, cursor.lastrowid)
    if created_tag is None:
        raise RuntimeError("Tag was created but could not be retrieved.")

    return created_tag


def get_tag_by_id(cursor, tag_id: int) -> Tag | None:
    cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
    row = cursor.fetchone()
    return _to_tag(row) if row else None


def get_tag_by_name(cursor, name: str) -> Tag | None:
    normalized_name = normalize_tag_name(name)
    cursor.execute(
        "SELECT * FROM tags WHERE lower(name) = lower(?)",
        (normalized_name,),
    )
    row = cursor.fetchone()
    return _to_tag(row) if row else None


def get_tags(cursor, active_only: bool = False) -> list[Tag]:
    sql = "SELECT * FROM tags"
    params = []

    if active_only:
        sql += " WHERE is_active = ?"
        params.append(1)

    sql += " ORDER BY name"
    cursor.execute(sql, params)
    return [_to_tag(row) for row in cursor.fetchall()]


def update_tag(
    cursor,
    tag_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> Tag | None:
    updates, params = [], []

    tag = get_tag_by_id(cursor, tag_id)
    if tag is None:
        return None

    if name is not None:
        updates.append("name = ?")
        params.append(normalize_tag_name(name))
    if description is not None:
        updates.append("description = ?")
        params.append(normalize_description(description))
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(normalize_is_active(is_active))

    if not updates:
        return tag

    params.append(tag_id)
    query = f"UPDATE tags SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))

    return get_tag_by_id(cursor, tag_id)


def delete_tag(cursor, tag_id: int) -> bool:
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    return cursor.rowcount > 0


def count_invoices_for_tag(cursor, tag_id: int) -> int:
    cursor.execute(
        "SELECT COUNT(*) AS invoice_count FROM invoice_tags WHERE tag_id = ?",
        (tag_id,),
    )
    row = cursor.fetchone()
    return row["invoice_count"] if row else 0


def add_tag_to_invoice(cursor, invoice_id: int, tag_id: int) -> InvoiceTag:
    cursor.execute(
        """
        INSERT INTO invoice_tags (invoice_id, tag_id)
        VALUES (?, ?)
        """,
        (invoice_id, tag_id),
    )

    invoice_tag = get_invoice_tag(cursor, invoice_id, tag_id)
    if invoice_tag is None:
        raise RuntimeError("Invoice tag was created but could not be retrieved.")

    return invoice_tag


def get_invoice_tag(cursor, invoice_id: int, tag_id: int) -> InvoiceTag | None:
    cursor.execute(
        """
        SELECT *
        FROM invoice_tags
        WHERE invoice_id = ? AND tag_id = ?
        """,
        (invoice_id, tag_id),
    )
    row = cursor.fetchone()
    return _to_invoice_tag(row) if row else None


def get_tags_for_invoice(cursor, invoice_id: int) -> list[Tag]:
    cursor.execute(
        """
        SELECT tags.*
        FROM tags
        JOIN invoice_tags ON invoice_tags.tag_id = tags.id
        WHERE invoice_tags.invoice_id = ?
        ORDER BY tags.name
        """,
        (invoice_id,),
    )
    return [_to_tag(row) for row in cursor.fetchall()]


def remove_tag_from_invoice(cursor, invoice_id: int, tag_id: int) -> bool:
    cursor.execute(
        """
        DELETE FROM invoice_tags
        WHERE invoice_id = ? AND tag_id = ?
        """,
        (invoice_id, tag_id),
    )
    return cursor.rowcount > 0
