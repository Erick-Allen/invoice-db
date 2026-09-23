import pytest

from invoice_db.services import customer_locations
from invoice_db.services import exceptions
from invoice_db.services import suppliers


def _create_location(cursor, customer_id: int, **overrides):
    values = {
        "customer_id": customer_id,
        "label": "Home",
        "address_line1": "123 Main St",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32801",
    }
    values.update(overrides)
    return customer_locations.create_customer_location(cursor, **values)


def _create_supplier_location(cursor, supplier_id: int, **overrides):
    values = {
        "supplier_id": supplier_id,
        "label": "Counter",
        "address_line1": "789 Supplier Way",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32803",
    }
    values.update(overrides)
    return customer_locations.create_supplier_location(cursor, **values)


def test_create_customer_location(cursor, customer_john):
    location = _create_location(cursor, customer_john)

    assert location["customer_id"] == customer_john
    assert location["location_id"] > 0
    assert location["label"] == "Home"
    assert location["country"] == "US"
    assert location["is_primary"] is True


def test_list_customer_locations(cursor, customer_john):
    _create_location(cursor, customer_john, label="Home")
    _create_location(cursor, customer_john, label="Shop", address_line1="456 Shop Rd")

    locations = customer_locations.list_customer_locations(cursor, customer_id=customer_john)

    assert [location["label"] for location in locations] == ["Home", "Shop"]


def test_update_customer_location(cursor, customer_john):
    location = _create_location(cursor, customer_john)

    updated = customer_locations.update_customer_location_by_id(
        cursor,
        customer_id=customer_john,
        location_id=location["id"],
        label="Main Office",
        notes="Call first",
    )

    assert updated["label"] == "Main Office"
    assert updated["notes"] == "Call first"


def test_deactivate_customer_location(cursor, customer_john):
    location = _create_location(cursor, customer_john)

    deactivated = customer_locations.deactivate_customer_location(
        cursor,
        customer_id=customer_john,
        location_id=location["id"],
    )

    assert deactivated["is_active"] is False
    assert deactivated["is_primary"] is False


def test_delete_customer_location(cursor, customer_john):
    location = _create_location(cursor, customer_john)

    customer_locations.delete_customer_location(
        cursor,
        customer_id=customer_john,
        location_id=location["id"],
    )

    with pytest.raises(exceptions.NotFoundError):
        customer_locations.get_customer_location_by_id(
            cursor,
            customer_id=customer_john,
            location_id=location["id"],
        )


def test_delete_customer_location_keeps_location_available(cursor, customer_john):
    location = _create_location(cursor, customer_john)

    customer_locations.delete_customer_location(
        cursor,
        customer_id=customer_john,
        location_id=location["id"],
    )

    locations = customer_locations.list_locations(cursor)

    assert locations == [
        {
            "id": location["location_id"],
            "address_line1": "123 Main St",
            "address_line2": None,
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
            "country": "US",
            "assigned_customer_count": 0,
            "assigned_customer_names": None,
            "assigned_supplier_count": 0,
            "assigned_supplier_names": None,
            "assigned_count": 0,
            "assigned_names": None,
            "created_at": locations[0]["created_at"],
            "updated_at": locations[0]["updated_at"],
        }
    ]


def test_create_standalone_location(cursor):
    location = customer_locations.create_location(
        cursor,
        address_line1="789 Standalone Ave",
        city="Orlando",
        state="FL",
        postal_code="32804",
    )

    assert location["address_line1"] == "789 Standalone Ave"
    assert location["assigned_customer_count"] == 0
    assert location["assigned_count"] == 0


def test_create_standalone_location_rejects_duplicate_address(cursor):
    customer_locations.create_location(
        cursor,
        address_line1="789 Standalone Ave",
        city="Orlando",
        state="FL",
        postal_code="32804",
    )

    with pytest.raises(exceptions.ValidationError, match="already exists"):
        customer_locations.create_location(
            cursor,
            address_line1=" 789 standalone ave ",
            city="Orlando",
            state="FL",
            postal_code="32804",
        )


def test_location_must_belong_to_customer(cursor, customer_john, customer_alice):
    location = _create_location(cursor, customer_john)

    with pytest.raises(exceptions.ValidationError, match="does not belong"):
        customer_locations.get_customer_location_by_id(
            cursor,
            customer_id=customer_alice,
            location_id=location["id"],
        )


def test_create_customer_location_reuses_existing_global_address(cursor, customer_john, customer_alice):
    first = _create_location(cursor, customer_john)
    second = _create_location(cursor, customer_alice, label="Office", address_line1="123 MAIN ST")

    assert second["location_id"] == first["location_id"]


def test_create_customer_location_rejects_duplicate_address_for_same_customer(cursor, customer_john):
    _create_location(cursor, customer_john)

    with pytest.raises(exceptions.ValidationError, match="already assigned to this customer"):
        _create_location(cursor, customer_john, label="Office", address_line1="123 MAIN ST")


def test_create_customer_location_requires_customer(cursor):
    with pytest.raises(exceptions.ValidationError, match="Customer id must be a positive integer"):
        _create_location(cursor, 0)


def test_create_supplier_location(cursor):
    supplier = suppliers.create_supplier(cursor, name="Johnstone")

    location = _create_supplier_location(cursor, supplier["id"])

    assert location["supplier_id"] == supplier["id"]
    assert location["location_id"] > 0
    assert location["label"] == "Counter"
    assert location["country"] == "US"
    assert location["is_primary"] is True


def test_list_supplier_locations(cursor):
    supplier = suppliers.create_supplier(cursor, name="Johnstone")
    _create_supplier_location(cursor, supplier["id"], label="Counter")
    _create_supplier_location(cursor, supplier["id"], label="Warehouse", address_line1="456 Warehouse Rd")

    locations = customer_locations.list_supplier_locations(cursor, supplier_id=supplier["id"])

    assert [location["label"] for location in locations] == ["Counter", "Warehouse"]


def test_delete_supplier_location_keeps_location_available(cursor):
    supplier = suppliers.create_supplier(cursor, name="Johnstone")
    location = _create_supplier_location(cursor, supplier["id"])

    customer_locations.delete_supplier_location(
        cursor,
        supplier_id=supplier["id"],
        location_id=location["id"],
    )

    locations = customer_locations.list_locations(cursor)

    assert locations[0]["id"] == location["location_id"]


def test_location_detail_includes_supplier_assignments(cursor):
    supplier = suppliers.create_supplier(cursor, name="Johnstone", phone="555-0100", email="source@example.com")
    location = _create_supplier_location(cursor, supplier["id"])

    detail = customer_locations.get_location_detail(cursor, location_id=location["location_id"])

    assert detail["supplier_assignments"][0]["supplier_id"] == supplier["id"]
    assert detail["supplier_assignments"][0]["supplier_name"] == "Johnstone"
    assert detail["supplier_assignments"][0]["supplier_phone"] == "555-0100"


def test_supplier_location_must_belong_to_supplier(cursor):
    supplier = suppliers.create_supplier(cursor, name="Johnstone")
    other_supplier = suppliers.create_supplier(cursor, name="Carrier")
    location = _create_supplier_location(cursor, supplier["id"])

    with pytest.raises(exceptions.ValidationError, match="does not belong"):
        customer_locations.get_supplier_location_by_id(
            cursor,
            supplier_id=other_supplier["id"],
            location_id=location["id"],
        )
