from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class BusinessDocumentCreate:
    workspace_id: int
    title: str
    category: str
    content_json: str
    content_text: str


@dataclass
class BusinessDocument:
    id: int
    workspace_id: int
    title: str
    category: str
    content_json: str
    content_text: str
    created_at: str
    updated_at: str


def _to_business_document(row: Row) -> BusinessDocument:
    return BusinessDocument(
        id=row["id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        category=row["category"],
        content_json=row["content_json"],
        content_text=row["content_text"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_business_document(cursor, document: BusinessDocumentCreate) -> BusinessDocument:
    cursor.execute(
        """
        INSERT INTO business_documents (
            workspace_id,
            title,
            category,
            content_json,
            content_text
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            document.workspace_id,
            document.title,
            document.category,
            document.content_json,
            document.content_text,
        ),
    )

    created_document = get_business_document_by_id(
        cursor,
        cursor.lastrowid,
        workspace_id=document.workspace_id,
    )
    if created_document is None:
        raise RuntimeError("Business document was created but could not be retrieved.")

    return created_document


def get_business_documents(cursor, *, workspace_id: int) -> list[BusinessDocument]:
    cursor.execute(
        """
        SELECT *
        FROM business_documents
        WHERE workspace_id = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (workspace_id,),
    )
    return [_to_business_document(row) for row in cursor.fetchall()]


def get_business_document_by_id(
    cursor,
    document_id: int,
    *,
    workspace_id: int,
) -> BusinessDocument | None:
    cursor.execute(
        """
        SELECT *
        FROM business_documents
        WHERE id = ? AND workspace_id = ?
        """,
        (document_id, workspace_id),
    )
    row = cursor.fetchone()
    return _to_business_document(row) if row else None


def update_business_document(
    cursor,
    document_id: int,
    *,
    workspace_id: int,
    updates: dict,
) -> BusinessDocument | None:
    document = get_business_document_by_id(
        cursor,
        document_id,
        workspace_id=workspace_id,
    )
    if document is None:
        return None

    allowed_fields = {"title", "category", "content_json", "content_text"}
    update_fields = [field for field in allowed_fields if field in updates]
    if not update_fields:
        return document

    assignments = ", ".join(f"{field} = ?" for field in update_fields)
    values = [updates[field] for field in update_fields]
    cursor.execute(
        f"""
        UPDATE business_documents
        SET {assignments}
        WHERE id = ? AND workspace_id = ?
        """,
        (*values, document_id, workspace_id),
    )

    return get_business_document_by_id(
        cursor,
        document_id,
        workspace_id=workspace_id,
    )


def delete_business_document(cursor, document_id: int, *, workspace_id: int) -> bool:
    cursor.execute(
        """
        DELETE FROM business_documents
        WHERE id = ? AND workspace_id = ?
        """,
        (document_id, workspace_id),
    )
    return cursor.rowcount > 0
