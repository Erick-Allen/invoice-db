import pytest

from invoice_db.db import customer_locations
from invoice_db.db import suppliers
from invoice_db.db.suppliers import SupplierCreate


def _location_create(customer_id: int, **overrides):
    values = {
        "customer_id": customer_id,
        "label": "Home",
        "address_line1": "123 Main St",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32801",
    }
    values.update(overrides)
    return customer_locations.CustomerLocationCreate(**values)


def _supplier_location_create(supplier_id: int, **overrides):
    values = {
        "supplier_id": supplier_id,
        "label": "Counter",
        "address_line1": "789 Supplier Way",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32803",
    }
    values.update(overrides)
    return customer_locations.SupplierLocationCreate(**values)


def _supplier(cursor, name="Johnstone"):
    return suppliers.create_supplier(cursor, SupplierCreate(name=name))


def test_create_customer_location_defaults_first_location_to_primary(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    assert location.id > 0
    assert location.customer_id == customer_john
    assert location.location_id > 0
    assert location.label == "Home"
    assert location.country == "US"
    assert location.is_primary
    assert location.is_active


def test_create_second_primary_location_clears_previous_primary(cursor, customer_john):
    first = customer_locations.create_customer_location(cursor, _location_create(customer_john, label="Home"))
    second = customer_locations.create_customer_location(
        cursor,
        _location_create(customer_john, label="Shop", address_line1="456 Shop Rd", is_primary=True),
    )

    reloaded_first = customer_locations.get_customer_location_by_id(cursor, first.id)

    assert not reloaded_first.is_primary
    assert second.is_primary


def test_get_customer_locations_orders_primary_first(cursor, customer_john):
    customer_locations.create_customer_location(cursor, _location_create(customer_john, label="Home"))
    primary = customer_locations.create_customer_location(
        cursor,
        _location_create(customer_john, label="Office", address_line1="456 Office Rd", is_primary=True),
    )

    rows = customer_locations.get_customer_locations(cursor, customer_john)

    assert rows[0].id == primary.id
    assert [row.label for row in rows] == ["Office", "Home"]


def test_get_customer_locations_can_filter_active_only(cursor, customer_john):
    customer_locations.create_customer_location(cursor, _location_create(customer_john, label="Home"))
    customer_locations.create_customer_location(
        cursor,
        _location_create(customer_john, label="Old", address_line1="456 Old Rd", is_active=False),
    )

    rows = customer_locations.get_customer_locations(cursor, customer_john, active_only=True)

    assert len(rows) == 1
    assert rows[0].label == "Home"


def test_update_customer_location(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    updated = customer_locations.update_customer_location(
        cursor,
        location.id,
        label="Main Office",
        address_line2="Suite 200",
        notes="Use rear entrance",
    )

    assert updated.label == "Main Office"
    assert updated.address_line2 == "Suite 200"
    assert updated.notes == "Use rear entrance"


def test_update_location_updates_global_address_for_assignments(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    updated = customer_locations.update_location(
        cursor,
        location.location_id,
        address_line1="456 New Rd",
        city="Winter Park",
        state="FL",
        postal_code="32789",
    )
    reloaded_customer_location = customer_locations.get_customer_location_by_id(cursor, location.id)

    assert updated.address_line1 == "456 New Rd"
    assert updated.city == "Winter Park"
    assert reloaded_customer_location.address_line1 == "456 New Rd"
    assert reloaded_customer_location.city == "Winter Park"


def test_update_location_rejects_duplicate_global_address(cursor, customer_john):
    first = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    second = customer_locations.create_location(
        cursor,
        customer_locations.LocationCreate(
            address_line1="456 New Rd",
            city="Orlando",
            state="FL",
            postal_code="32802",
        ),
    )

    with pytest.raises(ValueError, match="That location already exists."):
        customer_locations.update_location(
            cursor,
            second.id,
            address_line1=first.address_line1,
            city=first.city,
            state=first.state,
            postal_code=first.postal_code,
            country=first.country,
        )


def test_location_belongs_to_customer(cursor, customer_john, customer_alice):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    assert customer_locations.location_belongs_to_customer(cursor, location.id, customer_john)
    assert not customer_locations.location_belongs_to_customer(cursor, location.id, customer_alice)


def test_delete_customer_location(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    assert customer_locations.delete_customer_location(cursor, location.id)
    assert customer_locations.get_customer_location_by_id(cursor, location.id) is None


def test_delete_customer_location_keeps_global_location(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))

    assert customer_locations.delete_customer_location(cursor, location.id)

    row = cursor.execute("SELECT id FROM locations WHERE id = ?", (location.location_id,)).fetchone()
    assert row is not None


def test_get_locations_includes_unassigned_locations(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    customer_locations.delete_customer_location(cursor, location.id)

    rows = customer_locations.get_locations(cursor)

    assert len(rows) == 1
    assert rows[0].id == location.location_id
    assert rows[0].assigned_customer_count == 0
    assert rows[0].assigned_customer_names is None


def test_get_locations_generalizes_customer_and_supplier_assignments(cursor, customer_john):
    location = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    supplier = _supplier(cursor)
    customer_locations.create_supplier_location(
        cursor,
        _supplier_location_create(
            supplier.id,
            address_line1=location.address_line1,
            city=location.city,
            state=location.state,
            postal_code=location.postal_code,
            country=location.country,
        ),
    )

    rows = customer_locations.get_locations(cursor)
    row = next(row for row in rows if row.id == location.location_id)

    assert row.assigned_customer_count == 1
    assert row.assigned_supplier_count == 1
    assert row.assigned_count == 2
    assert row.assigned_customer_names == "John"
    assert row.assigned_supplier_names == "Johnstone"
    assert row.assigned_names == "John, Johnstone"


def test_create_standalone_location(cursor):
    location = customer_locations.create_location(
        cursor,
        customer_locations.LocationCreate(
            address_line1="789 Standalone Ave",
            city="Orlando",
            state="FL",
            postal_code="32804",
        ),
    )

    assert location.id > 0
    assert location.address_line1 == "789 Standalone Ave"
    assert location.assigned_customer_count == 0


def test_create_standalone_location_rejects_duplicate_address(cursor):
    customer_locations.create_location(
        cursor,
        customer_locations.LocationCreate(
            address_line1="789 Standalone Ave",
            city="Orlando",
            state="FL",
            postal_code="32804",
        ),
    )

    with pytest.raises(ValueError, match="already exists"):
        customer_locations.create_location(
            cursor,
            customer_locations.LocationCreate(
                address_line1=" 789 standalone ave ",
                city="Orlando",
                state="FL",
                postal_code="32804",
            ),
        )


def test_create_customer_location_reuses_existing_global_address(cursor, customer_john, customer_alice):
    first = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    second = customer_locations.create_customer_location(
        cursor,
        _location_create(customer_alice, label="Office", address_line1=" 123 main st "),
    )

    assert second.location_id == first.location_id


def test_create_customer_location_rejects_duplicate_address_for_same_customer(cursor, customer_john):
    customer_locations.create_customer_location(cursor, _location_create(customer_john))

    with pytest.raises(ValueError, match="already assigned to this customer"):
        customer_locations.create_customer_location(
            cursor,
            _location_create(customer_john, label="Office", address_line1="123 MAIN ST"),
        )


def test_update_customer_location_rejects_duplicate_address_for_same_customer(cursor, customer_john):
    existing = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    duplicate = customer_locations.create_customer_location(
        cursor,
        _location_create(customer_john, label="Office", address_line1="456 Office Rd"),
    )

    with pytest.raises(ValueError, match="already assigned to this customer"):
        customer_locations.update_customer_location(
            cursor,
            duplicate.id,
            address_line1=existing.address_line1,
            city=existing.city,
            state=existing.state,
            postal_code=existing.postal_code,
        )


def test_create_location_requires_existing_customer(cursor):
    with pytest.raises(ValueError, match="Customer not found"):
        customer_locations.create_customer_location(cursor, _location_create(9999))


def test_create_supplier_location_defaults_first_location_to_primary(cursor):
    supplier = _supplier(cursor)

    location = customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id))

    assert location.id > 0
    assert location.supplier_id == supplier.id
    assert location.location_id > 0
    assert location.label == "Counter"
    assert location.country == "US"
    assert location.is_primary
    assert location.is_active


def test_create_second_primary_supplier_location_clears_previous_primary(cursor):
    supplier = _supplier(cursor)
    first = customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id, label="Counter"))
    second = customer_locations.create_supplier_location(
        cursor,
        _supplier_location_create(supplier.id, label="Warehouse", address_line1="456 Warehouse Rd", is_primary=True),
    )

    reloaded_first = customer_locations.get_supplier_location_by_id(cursor, first.id)

    assert not reloaded_first.is_primary
    assert second.is_primary


def test_get_supplier_locations_orders_primary_first(cursor):
    supplier = _supplier(cursor)
    customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id, label="Counter"))
    primary = customer_locations.create_supplier_location(
        cursor,
        _supplier_location_create(supplier.id, label="Warehouse", address_line1="456 Warehouse Rd", is_primary=True),
    )

    rows = customer_locations.get_supplier_locations(cursor, supplier.id)

    assert rows[0].id == primary.id
    assert [row.label for row in rows] == ["Warehouse", "Counter"]


def test_delete_supplier_location_keeps_global_location(cursor):
    supplier = _supplier(cursor)
    location = customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id))

    assert customer_locations.delete_supplier_location(cursor, location.id)

    row = cursor.execute("SELECT id FROM locations WHERE id = ?", (location.location_id,)).fetchone()
    assert row is not None


def test_create_supplier_location_reuses_existing_global_address(cursor, customer_john):
    customer_location = customer_locations.create_customer_location(cursor, _location_create(customer_john))
    supplier = _supplier(cursor)

    supplier_location = customer_locations.create_supplier_location(
        cursor,
        _supplier_location_create(supplier.id, address_line1=" 123 main st ", city="Orlando", postal_code="32801"),
    )

    assert supplier_location.location_id == customer_location.location_id


def test_create_supplier_location_rejects_duplicate_address_for_same_supplier(cursor):
    supplier = _supplier(cursor)
    customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id))

    with pytest.raises(ValueError, match="already assigned to this supplier"):
        customer_locations.create_supplier_location(
            cursor,
            _supplier_location_create(supplier.id, label="Warehouse", address_line1="789 SUPPLIER WAY"),
        )


def test_get_location_supplier_assignments(cursor):
    supplier = _supplier(cursor)
    location = customer_locations.create_supplier_location(cursor, _supplier_location_create(supplier.id))

    assignments = customer_locations.get_location_supplier_assignments(cursor, location.location_id)

    assert len(assignments) == 1
    assert assignments[0].supplier_id == supplier.id
    assert assignments[0].supplier_name == "Johnstone"
