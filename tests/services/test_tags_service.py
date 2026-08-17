import pytest

from invoice_db.services import exceptions
from invoice_db.services import tags as tag_services


def test_create_and_list_tags(cursor):
    tag = tag_services.create_tag(
        cursor,
        name=" Commercial ",
        description=" Job context ",
    )

    result = tag_services.list_tags(cursor)

    assert tag["name"] == "Commercial"
    assert tag["description"] == "Job context"
    assert tag["id"] in {existing_tag["id"] for existing_tag in result}


def test_create_duplicate_tag_raises_clear_validation_error(cursor):
    tag_services.create_tag(cursor, name="Commercial")

    with pytest.raises(exceptions.ValidationError, match='A tag named "Commercial" already exists.'):
        tag_services.create_tag(cursor, name="commercial")


def test_update_tag_duplicate_name_raises_clear_validation_error(cursor):
    tag_services.create_tag(cursor, name="Commercial")
    repair = tag_services.create_tag(cursor, name="Repair")

    with pytest.raises(exceptions.ValidationError, match='A tag named "Commercial" already exists.'):
        tag_services.update_tag_by_id(cursor, repair["id"], name="commercial")


def test_deactivate_tag(cursor):
    tag = tag_services.create_tag(cursor, name="Repair")

    updated = tag_services.deactivate_tag(cursor, tag["id"])

    assert updated["is_active"] is False


def test_delete_unused_tag(cursor):
    tag = tag_services.create_tag(cursor, name="Repair")

    tag_services.delete_tag(cursor, tag["id"])

    with pytest.raises(exceptions.NotFoundError):
        tag_services.get_tag_by_id(cursor, tag["id"])


def test_delete_tag_with_invoice_raises_conflict(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair")
    tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])

    with pytest.raises(exceptions.ConflictError, match='Cannot delete tag "Repair" because 1 invoice uses it.'):
        tag_services.delete_tag(cursor, tag["id"])


def test_add_tag_to_invoice(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair")

    invoice_tag = tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])
    result = tag_services.list_invoice_tags(cursor, invoice_john)

    assert invoice_tag["invoice_id"] == invoice_john
    assert invoice_tag["tag_id"] == tag["id"]
    assert [tag["name"] for tag in result] == ["Repair"]


def test_add_tag_to_invoice_rejects_inactive_tag(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair", is_active=False)

    with pytest.raises(exceptions.ValidationError, match="Inactive tags cannot be added to invoices."):
        tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])


def test_add_tag_to_invoice_rejects_duplicate_assignment(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair")
    tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])

    with pytest.raises(exceptions.ConflictError, match='Tag "Repair" is already attached to invoice'):
        tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])


def test_remove_tag_from_invoice(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair")
    tag_services.add_tag_to_invoice(cursor, invoice_john, tag["id"])

    tag_services.remove_tag_from_invoice(cursor, invoice_john, tag["id"])

    assert tag_services.list_invoice_tags(cursor, invoice_john) == []


def test_remove_missing_tag_assignment_raises_not_found(cursor, invoice_john):
    tag = tag_services.create_tag(cursor, name="Repair")

    with pytest.raises(exceptions.NotFoundError):
        tag_services.remove_tag_from_invoice(cursor, invoice_john, tag["id"])


def test_invoice_tag_operations_validate_invoice(cursor):
    tag = tag_services.create_tag(cursor, name="Repair")

    with pytest.raises(exceptions.NotFoundError):
        tag_services.add_tag_to_invoice(cursor, 9999, tag["id"])

    with pytest.raises(exceptions.NotFoundError):
        tag_services.list_invoice_tags(cursor, 9999)
