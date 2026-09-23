import pytest


def test_customer_locations_table_exists(cursor):
    row = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'customer_locations'
        """
    ).fetchone()

    assert row is not None


def test_locations_table_exists(cursor):
    row = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'locations'
        """
    ).fetchone()

    assert row is not None


def test_supplier_locations_table_exists(cursor):
    row = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'supplier_locations'
        """
    ).fetchone()

    assert row is not None


def _insert_location(cursor, **overrides):
    values = {
        "address_line1": "123 Main St",
        "address_line2": None,
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32801",
        "country": "US",
    }
    values.update(overrides)
    return cursor.execute(
        """
        INSERT INTO locations (address_line1, address_line2, city, state, postal_code, country)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            values["address_line1"],
            values["address_line2"],
            values["city"],
            values["state"],
            values["postal_code"],
            values["country"],
        ),
    ).lastrowid


def test_customer_locations_required_fields(cursor, customer_john):
    location_id = _insert_location(cursor)

    with pytest.raises(Exception):
        cursor.execute(
            """
            INSERT INTO customer_locations (customer_id, location_id, label)
            VALUES (?, ?, ?)
            """,
            (customer_john, location_id, ""),
        )


def test_customer_locations_delete_with_customer(cursor, customer_john):
    location_id = _insert_location(cursor)
    cursor.execute(
        """
        INSERT INTO customer_locations (customer_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (customer_john, location_id, "Home"),
    )

    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_john,))
    row = cursor.execute("SELECT * FROM customer_locations WHERE customer_id = ?", (customer_john,)).fetchone()

    assert row is None


def test_invoices_can_reference_customer_location(cursor, customer_john):
    global_location_id = _insert_location(cursor)
    location_id = cursor.execute(
        """
        INSERT INTO customer_locations (customer_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (customer_john, global_location_id, "Home"),
    ).lastrowid

    cursor.execute(
        """
        INSERT INTO invoices (customer_id, location_id, total, status)
        VALUES (?, ?, ?, ?)
        """,
        (customer_john, location_id, 0, "draft"),
    )

    invoice = cursor.execute("SELECT location_id FROM invoices").fetchone()

    assert invoice["location_id"] == location_id


def test_locations_addresses_are_globally_unique(cursor):
    _insert_location(cursor, address_line1="123 Main St")

    with pytest.raises(Exception):
        _insert_location(cursor, address_line1=" 123 main st ")


def test_customer_location_can_be_shared_across_customers(cursor, customer_john, customer_alice):
    location_id = _insert_location(cursor)
    cursor.execute(
        """
        INSERT INTO customer_locations (customer_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (customer_john, location_id, "Home"),
    )
    cursor.execute(
        """
        INSERT INTO customer_locations (customer_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (customer_alice, location_id, "Office"),
    )

    count = cursor.execute("SELECT COUNT(*) AS total FROM customer_locations").fetchone()

    assert count["total"] == 2


def test_customer_location_can_only_claim_location_once_per_customer(cursor, customer_john):
    location_id = _insert_location(cursor)
    cursor.execute(
        """
        INSERT INTO customer_locations (customer_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (customer_john, location_id, "Home"),
    )
    with pytest.raises(Exception):
        cursor.execute(
            """
            INSERT INTO customer_locations (customer_id, location_id, label)
            VALUES (?, ?, ?)
            """,
            (customer_john, location_id, "Office"),
        )


def test_supplier_location_can_only_claim_location_once_per_supplier(cursor):
    supplier_id = cursor.execute("INSERT INTO suppliers (name) VALUES (?)", ("Johnstone",)).lastrowid
    location_id = _insert_location(cursor)
    cursor.execute(
        """
        INSERT INTO supplier_locations (supplier_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (supplier_id, location_id, "Counter"),
    )

    with pytest.raises(Exception):
        cursor.execute(
            """
            INSERT INTO supplier_locations (supplier_id, location_id, label)
            VALUES (?, ?, ?)
            """,
            (supplier_id, location_id, "Warehouse"),
        )


def test_supplier_locations_delete_with_supplier(cursor):
    supplier_id = cursor.execute("INSERT INTO suppliers (name) VALUES (?)", ("Johnstone",)).lastrowid
    location_id = _insert_location(cursor)
    cursor.execute(
        """
        INSERT INTO supplier_locations (supplier_id, location_id, label)
        VALUES (?, ?, ?)
        """,
        (supplier_id, location_id, "Counter"),
    )

    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    row = cursor.execute("SELECT * FROM supplier_locations WHERE supplier_id = ?", (supplier_id,)).fetchone()

    assert row is None
