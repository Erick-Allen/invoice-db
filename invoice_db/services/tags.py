import sqlite3
from typing import TypedDict

from invoice_db.db import invoices as invoices_db
from invoice_db.db import tags as tags_db
from invoice_db.db.validators import validate_positive_id
from . import exceptions


class TagRecord(TypedDict):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


class InvoiceTagRecord(TypedDict):
    invoice_id: int
    tag_id: int
    created_at: str


def _to_tag_record(tag: tags_db.Tag) -> TagRecord:
    return {
        "id": tag.id,
        "name": tag.name,
        "description": tag.description,
        "is_active": tag.is_active,
        "created_at": tag.created_at,
        "updated_at": tag.updated_at,
    }


def _to_invoice_tag_record(invoice_tag: tags_db.InvoiceTag) -> InvoiceTagRecord:
    return {
        "invoice_id": invoice_tag.invoice_id,
        "tag_id": invoice_tag.tag_id,
        "created_at": invoice_tag.created_at,
    }


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _validate_id(value: int, label: str) -> None:
    try:
        validate_positive_id(value, label)
    except ValueError as e:
        raise _as_validation_error(e) from e


def _require_invoice(cursor, invoice_id: int) -> sqlite3.Row:
    _validate_id(invoice_id, "Invoice id")
    invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)
    if invoice is None:
        raise exceptions.NotFoundError(f"Invoice not found (id={invoice_id})")
    return invoice


def _require_tag(cursor, tag_id: int) -> tags_db.Tag:
    _validate_id(tag_id, "Tag id")
    tag = tags_db.get_tag_by_id(cursor, tag_id)
    if tag is None:
        raise exceptions.NotFoundError(f"Tag not found (id={tag_id})")
    return tag


def _raise_if_tag_name_exists(
    cursor,
    name: str,
    *,
    current_tag_id: int | None = None,
) -> None:
    existing_tag = tags_db.get_tag_by_name(cursor, name)
    if existing_tag is not None and existing_tag.id != current_tag_id:
        raise exceptions.ValidationError(f'A tag named "{existing_tag.name}" already exists.')


def create_tag(
    cursor,
    name: str,
    description: str | None = None,
    is_active: bool = True,
) -> TagRecord:
    try:
        _raise_if_tag_name_exists(cursor, name)
        tag = tags_db.create_tag(
            cursor,
            tags_db.TagCreate(
                name=name,
                description=description,
                is_active=is_active,
            ),
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid tag data.") from e

    return _to_tag_record(tag)


def list_tags(cursor, active_only: bool = False) -> list[TagRecord]:
    return [
        _to_tag_record(tag)
        for tag in tags_db.get_tags(cursor, active_only=active_only)
    ]


def get_tag_by_id(cursor, tag_id: int) -> TagRecord:
    return _to_tag_record(_require_tag(cursor, tag_id))


def update_tag_by_id(
    cursor,
    tag_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> TagRecord:
    _require_tag(cursor, tag_id)

    if name is None and description is None and is_active is None:
        raise exceptions.ValidationError("Please provide at least one value to update the tag.")

    try:
        if name is not None:
            _raise_if_tag_name_exists(cursor, name, current_tag_id=tag_id)

        updated_tag = tags_db.update_tag(
            cursor,
            tag_id=tag_id,
            name=name,
            description=description,
            is_active=is_active,
        )
    except ValueError as e:
        raise _as_validation_error(e) from e
    except sqlite3.IntegrityError as e:
        raise exceptions.ValidationError("Invalid tag update data.") from e

    if updated_tag is None:
        raise exceptions.ServiceError(f"Failed to update tag {tag_id}.")

    return _to_tag_record(updated_tag)


def deactivate_tag(cursor, tag_id: int) -> TagRecord:
    tag = _require_tag(cursor, tag_id)
    if not tag.is_active:
        raise exceptions.ValidationError("Tag is already inactive.")

    return update_tag_by_id(cursor, tag_id, is_active=False)


def delete_tag(cursor, tag_id: int) -> None:
    tag = _require_tag(cursor, tag_id)
    invoice_count = tags_db.count_invoices_for_tag(cursor, tag_id)

    if invoice_count > 0:
        invoice_word = "invoice" if invoice_count == 1 else "invoices"
        verb = "uses" if invoice_count == 1 else "use"
        raise exceptions.ConflictError(
            f'Cannot delete tag "{tag.name}" because {invoice_count} {invoice_word} {verb} it.'
        )

    deleted = tags_db.delete_tag(cursor, tag_id)
    if not deleted:
        raise exceptions.NotFoundError(f"Tag not found (id={tag_id})")


def add_tag_to_invoice(cursor, invoice_id: int, tag_id: int) -> InvoiceTagRecord:
    _require_invoice(cursor, invoice_id)
    tag = _require_tag(cursor, tag_id)

    if not tag.is_active:
        raise exceptions.ValidationError("Inactive tags cannot be added to invoices.")

    try:
        invoice_tag = tags_db.add_tag_to_invoice(cursor, invoice_id, tag_id)
    except sqlite3.IntegrityError as e:
        if tags_db.get_invoice_tag(cursor, invoice_id, tag_id) is not None:
            raise exceptions.ConflictError(f'Tag "{tag.name}" is already attached to invoice {invoice_id}.') from e
        raise exceptions.ValidationError("Invalid invoice tag data.") from e

    return _to_invoice_tag_record(invoice_tag)


def list_invoice_tags(cursor, invoice_id: int) -> list[TagRecord]:
    _require_invoice(cursor, invoice_id)
    return [
        _to_tag_record(tag)
        for tag in tags_db.get_tags_for_invoice(cursor, invoice_id)
    ]


def remove_tag_from_invoice(cursor, invoice_id: int, tag_id: int) -> None:
    _require_invoice(cursor, invoice_id)
    _require_tag(cursor, tag_id)

    removed = tags_db.remove_tag_from_invoice(cursor, invoice_id, tag_id)
    if not removed:
        raise exceptions.NotFoundError(
            f"Tag not attached to invoice (invoice_id={invoice_id}, tag_id={tag_id})"
        )
