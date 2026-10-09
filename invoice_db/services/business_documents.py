import json
import sqlite3
from typing import Any, TypedDict

from invoice_db.db import business_documents as business_documents_db
from invoice_db.db.validators import validate_positive_id

from . import exceptions

DEFAULT_CATEGORY = "General"


class BusinessDocumentRecord(TypedDict):
    id: int
    workspace_id: int
    title: str
    category: str
    content_json: dict[str, Any]
    content_text: str
    created_at: str
    updated_at: str


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _validate_id(value: int, label: str) -> None:
    try:
        validate_positive_id(value, label)
    except ValueError as e:
        raise _as_validation_error(e) from e


def _normalize_required_text(value: str | None, label: str) -> str:
    if value is None:
        raise exceptions.ValidationError(f"{label} is required.")

    normalized_value = " ".join(value.strip().split())
    if not normalized_value:
        raise exceptions.ValidationError(f"{label} is required.")

    return normalized_value


def _normalize_category(value: str | None) -> str:
    if value is None or not value.strip():
        return DEFAULT_CATEGORY
    return " ".join(value.strip().split())


def _validate_content_json(content_json: Any) -> dict[str, Any]:
    if not isinstance(content_json, dict):
        raise exceptions.ValidationError("Document content must be a JSON object.")
    if content_json.get("type") != "doc":
        raise exceptions.ValidationError("Document content must be a TipTap document.")
    return content_json


def _extract_text_node(node: Any) -> list[str]:
    if not isinstance(node, dict):
        return []

    node_text: list[str] = []
    text = node.get("text")
    if isinstance(text, str):
        node_text.append(text)

    for child in node.get("content", []) or []:
        node_text.extend(_extract_text_node(child))

    node_type = node.get("type")
    if node_type in {"paragraph", "heading", "listItem"} and node_text:
        node_text.append("\n")

    return node_text


def _extract_content_text(content_json: dict[str, Any]) -> str:
    text = "".join(_extract_text_node(content_json))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _serialize_content_json(content_json: dict[str, Any]) -> str:
    return json.dumps(content_json, separators=(",", ":"), sort_keys=True)


def _deserialize_content_json(content_json: str) -> dict[str, Any]:
    loaded_content = json.loads(content_json)
    if not isinstance(loaded_content, dict):
        raise RuntimeError("Stored business document content is invalid.")
    return loaded_content


def _to_document_record(
    document: business_documents_db.BusinessDocument,
) -> BusinessDocumentRecord:
    return {
        "id": document.id,
        "workspace_id": document.workspace_id,
        "title": document.title,
        "category": document.category,
        "content_json": _deserialize_content_json(document.content_json),
        "content_text": document.content_text,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


def create_business_document(
    cursor,
    *,
    workspace_id: int,
    title: str,
    content_json: dict[str, Any],
    category: str | None = None,
) -> BusinessDocumentRecord:
    _validate_id(workspace_id, "Workspace id")
    validated_content = _validate_content_json(content_json)

    try:
        document = business_documents_db.create_business_document(
            cursor,
            business_documents_db.BusinessDocumentCreate(
                workspace_id=workspace_id,
                title=_normalize_required_text(title, "Title"),
                category=_normalize_category(category),
                content_json=_serialize_content_json(validated_content),
                content_text=_extract_content_text(validated_content),
            ),
        )
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid business document data.") from e

    return _to_document_record(document)


def list_business_documents(cursor, *, workspace_id: int) -> list[BusinessDocumentRecord]:
    _validate_id(workspace_id, "Workspace id")
    return [
        _to_document_record(document)
        for document in business_documents_db.get_business_documents(
            cursor,
            workspace_id=workspace_id,
        )
    ]


def get_business_document_by_id(
    cursor,
    document_id: int,
    *,
    workspace_id: int,
) -> BusinessDocumentRecord:
    _validate_id(workspace_id, "Workspace id")
    _validate_id(document_id, "Document id")
    document = business_documents_db.get_business_document_by_id(
        cursor,
        document_id,
        workspace_id=workspace_id,
    )
    if document is None:
        raise exceptions.NotFoundError(f"Business document not found (id={document_id})")

    return _to_document_record(document)


def update_business_document_by_id(
    cursor,
    document_id: int,
    *,
    workspace_id: int,
    updates: dict[str, Any],
) -> BusinessDocumentRecord:
    _validate_id(workspace_id, "Workspace id")
    _validate_id(document_id, "Document id")

    normalized_updates: dict[str, Any] = {}
    if "title" in updates:
        normalized_updates["title"] = _normalize_required_text(updates["title"], "Title")
    if "category" in updates:
        normalized_updates["category"] = _normalize_category(updates["category"])
    if "content_json" in updates:
        validated_content = _validate_content_json(updates["content_json"])
        normalized_updates["content_json"] = _serialize_content_json(validated_content)
        normalized_updates["content_text"] = _extract_content_text(validated_content)

    document = business_documents_db.update_business_document(
        cursor,
        document_id,
        workspace_id=workspace_id,
        updates=normalized_updates,
    )
    if document is None:
        raise exceptions.NotFoundError(f"Business document not found (id={document_id})")

    return _to_document_record(document)


def delete_business_document_by_id(cursor, document_id: int, *, workspace_id: int) -> None:
    _validate_id(workspace_id, "Workspace id")
    _validate_id(document_id, "Document id")
    deleted = business_documents_db.delete_business_document(
        cursor,
        document_id,
        workspace_id=workspace_id,
    )
    if not deleted:
        raise exceptions.NotFoundError(f"Business document not found (id={document_id})")
