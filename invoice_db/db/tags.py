from dataclasses import dataclass
from sqlite3 import Row

from .validators import normalize_description, normalize_is_active, normalize_tag_name


@dataclass
class TagCreate:
    name: str
    description: str | None = None
    is_active: bool = True
    workspace_id: int | None = None


@dataclass
class Tag:
    id: int
    workspace_id: int | None
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
        workspace_id=row["workspace_id"],
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
        INSERT INTO tags (workspace_id, name, description, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (tag.workspace_id, name, description, is_active),
    )

    created_tag = get_tag_by_id(cursor, cursor.lastrowid, workspace_id=tag.workspace_id)
    if created_tag is None:
        raise RuntimeError("Tag was created but could not be retrieved.")

    return created_tag


def _workspace_filter(alias: str, workspace_id: int | None) -> tuple[str, list[int]]:
    if workspace_id is None:
        return f"{alias}.workspace_id IS NULL", []
    return f"{alias}.workspace_id = ?", [workspace_id]


def get_tag_by_id(
    cursor,
    tag_id: int,
    workspace_id: int | None = None,
) -> Tag | None:
    workspace_clause, workspace_params = _workspace_filter("tags", workspace_id)
    cursor.execute(
        f"SELECT * FROM tags WHERE id = ? AND {workspace_clause}",
        (tag_id, *workspace_params),
    )
    row = cursor.fetchone()
    return _to_tag(row) if row else None


def get_tag_by_name(
    cursor,
    name: str,
    workspace_id: int | None = None,
) -> Tag | None:
    normalized_name = normalize_tag_name(name)
    workspace_clause, workspace_params = _workspace_filter("tags", workspace_id)
    cursor.execute(
        f"SELECT * FROM tags WHERE lower(name) = lower(?) AND {workspace_clause}",
        (normalized_name, *workspace_params),
    )
    row = cursor.fetchone()
    return _to_tag(row) if row else None


def get_tags(
    cursor,
    active_only: bool = False,
    workspace_id: int | None = None,
) -> list[Tag]:
    workspace_clause, workspace_params = _workspace_filter("tags", workspace_id)
    sql = "SELECT * FROM tags"
    params = [*workspace_params]
    clauses = [workspace_clause]

    if active_only:
        clauses.append("is_active = ?")
        params.append(1)

    sql += " WHERE " + " AND ".join(clauses)
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
    workspace_id: int | None = None,
) -> Tag | None:
    updates, params = [], []

    tag = get_tag_by_id(cursor, tag_id, workspace_id=workspace_id)
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

    return get_tag_by_id(cursor, tag_id, workspace_id=workspace_id)


def delete_tag(
    cursor,
    tag_id: int,
    workspace_id: int | None = None,
) -> bool:
    if workspace_id is None:
        cursor.execute("DELETE FROM tags WHERE id = ? AND workspace_id IS NULL", (tag_id,))
    else:
        cursor.execute(
            "DELETE FROM tags WHERE id = ? AND workspace_id = ?",
            (tag_id, workspace_id),
        )
    return cursor.rowcount > 0


def count_invoices_for_tag(
    cursor,
    tag_id: int,
    workspace_id: int | None = None,
) -> int:
    workspace_clause, workspace_params = _workspace_filter("i", workspace_id)
    cursor.execute(
        f"""
        SELECT COUNT(*) AS invoice_count
        FROM invoice_tags it
        JOIN invoices i ON i.id = it.invoice_id
        WHERE it.tag_id = ? AND {workspace_clause}
        """,
        (tag_id, *workspace_params),
    )
    row = cursor.fetchone()
    return row["invoice_count"] if row else 0


def get_invoices_for_tag(
    cursor,
    tag_id: int,
    workspace_id: int | None = None,
) -> list[Row]:
    workspace_clause, workspace_params = _workspace_filter("i", workspace_id)
    cursor.execute(
        f"""
        WITH invoice_costs AS (
            SELECT
                invoice_id,
                COALESCE(SUM(quantity * unit_cost), 0) AS cost_total_cents
            FROM invoice_items
            GROUP BY invoice_id
        ),
        invoice_payments AS (
            SELECT
                invoice_id,
                COALESCE(SUM(amount_cents), 0) AS amount_paid_cents
            FROM payments
            GROUP BY invoice_id
        )
        SELECT
            i.id,
            i.invoice_number,
            i.customer_id,
            c.name AS customer_name,
            i.location_id,
            i.date_issued,
            i.date_due,
            i.total,
            i.status,
            COALESCE(ic.cost_total_cents, 0) AS cost_total_cents,
            COALESCE(ip.amount_paid_cents, 0) AS amount_paid_cents,
            MAX(i.total - COALESCE(ip.amount_paid_cents, 0), 0) AS balance_due_cents
        FROM invoice_tags it
        JOIN invoices i ON i.id = it.invoice_id
        JOIN customers c ON c.id = i.customer_id
        LEFT JOIN invoice_costs ic ON ic.invoice_id = i.id
        LEFT JOIN invoice_payments ip ON ip.invoice_id = i.id
        WHERE it.tag_id = ? AND {workspace_clause}
        ORDER BY COALESCE(i.date_issued, '') DESC, i.id DESC
        """,
        (tag_id, *workspace_params),
    )
    return cursor.fetchall()


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


def get_tags_for_invoice(
    cursor,
    invoice_id: int,
    workspace_id: int | None = None,
) -> list[Tag]:
    workspace_clause, workspace_params = _workspace_filter("tags", workspace_id)
    cursor.execute(
        f"""
        SELECT tags.*
        FROM tags
        JOIN invoice_tags ON invoice_tags.tag_id = tags.id
        WHERE invoice_tags.invoice_id = ? AND {workspace_clause}
        ORDER BY tags.name
        """,
        (invoice_id, *workspace_params),
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
