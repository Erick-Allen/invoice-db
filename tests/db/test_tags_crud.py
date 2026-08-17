import sqlite3

import pytest

from invoice_db.db import tags
from invoice_db.db.tags import TagCreate


def test_create_tag(cursor):
    tag = tags.create_tag(
        cursor,
        TagCreate(
            name="  Commercial  Repair ",
            description="  Job type  ",
        ),
    )

    assert tag.id > 0
    assert tag.name == "Commercial Repair"
    assert tag.description == "Job type"
    assert tag.is_active is True


def test_get_tag_by_name_is_case_insensitive(cursor):
    created = tags.create_tag(cursor, TagCreate(name="Commercial"))

    result = tags.get_tag_by_name(cursor, "commercial")

    assert result is not None
    assert result.id == created.id


def test_get_tags_active_only(cursor):
    active = tags.create_tag(cursor, TagCreate(name="Repair"))
    inactive = tags.create_tag(cursor, TagCreate(name="Archived", is_active=False))

    result = tags.get_tags(cursor, active_only=True)

    assert active.id in {tag.id for tag in result}
    assert inactive.id not in {tag.id for tag in result}


def test_update_tag(cursor):
    tag = tags.create_tag(cursor, TagCreate(name="Repair"))

    updated = tags.update_tag(
        cursor,
        tag.id,
        name="Roof",
        description="Roof jobs",
        is_active=False,
    )

    assert updated is not None
    assert updated.name == "Roof"
    assert updated.description == "Roof jobs"
    assert updated.is_active is False


def test_delete_tag(cursor):
    tag = tags.create_tag(cursor, TagCreate(name="Repair"))

    assert tags.delete_tag(cursor, tag.id) is True
    assert tags.get_tag_by_id(cursor, tag.id) is None


def test_add_and_list_invoice_tag(cursor, invoice_john):
    tag = tags.create_tag(cursor, TagCreate(name="Repair"))

    invoice_tag = tags.add_tag_to_invoice(cursor, invoice_john, tag.id)
    result = tags.get_tags_for_invoice(cursor, invoice_john)

    assert invoice_tag.invoice_id == invoice_john
    assert invoice_tag.tag_id == tag.id
    assert [tag.name for tag in result] == ["Repair"]


def test_remove_tag_from_invoice(cursor, invoice_john):
    tag = tags.create_tag(cursor, TagCreate(name="Repair"))
    tags.add_tag_to_invoice(cursor, invoice_john, tag.id)

    assert tags.remove_tag_from_invoice(cursor, invoice_john, tag.id) is True
    assert tags.get_tags_for_invoice(cursor, invoice_john) == []


def test_delete_tag_with_invoice_is_restricted(cursor, invoice_john):
    tag = tags.create_tag(cursor, TagCreate(name="Repair"))
    tags.add_tag_to_invoice(cursor, invoice_john, tag.id)

    with pytest.raises(sqlite3.IntegrityError):
        tags.delete_tag(cursor, tag.id)
