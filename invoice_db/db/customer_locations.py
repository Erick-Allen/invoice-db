from dataclasses import dataclass
from sqlite3 import Row

from .customers import assert_customer_exists
from .suppliers import get_supplier_by_id
from .validators import normalize_is_active, normalize_optional_customer_text, validate_positive_id


@dataclass
class CustomerLocationCreate:
    customer_id: int
    label: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    address_line2: str | None = None
    country: str = "US"
    is_primary: bool = False
    is_active: bool = True
    notes: str | None = None


@dataclass
class CustomerLocation:
    id: int
    customer_id: int
    location_id: int
    label: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


@dataclass
class SupplierLocationCreate:
    supplier_id: int
    label: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    address_line2: str | None = None
    country: str = "US"
    is_primary: bool = False
    is_active: bool = True
    notes: str | None = None


@dataclass
class SupplierLocation:
    id: int
    supplier_id: int
    location_id: int
    label: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


@dataclass
class Location:
    id: int
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    assigned_customer_count: int
    assigned_customer_names: str | None
    assigned_supplier_count: int
    assigned_supplier_names: str | None
    assigned_count: int
    assigned_names: str | None
    created_at: str
    updated_at: str


@dataclass
class LocationCreate:
    address_line1: str
    city: str
    state: str
    postal_code: str
    address_line2: str | None = None
    country: str = "US"


@dataclass
class LocationCustomerAssignment:
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    label: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


@dataclass
class LocationSupplierAssignment:
    id: int
    supplier_id: int
    supplier_name: str
    supplier_phone: str | None
    supplier_email: str | None
    label: str
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: str
    updated_at: str


@dataclass
class LocationInvoice:
    id: int
    customer_id: int
    customer_name: str
    customer_location_id: int
    date_issued: str | None
    date_due: str | None
    total: int
    status: str


def _normalize_required_text(value: str, label: str) -> str:
    normalized = normalize_optional_customer_text(value)
    if normalized is None:
        raise ValueError(f"{label} cannot be empty.")
    return normalized


def _to_customer_location(row: Row) -> CustomerLocation:
    return CustomerLocation(
        id=row["id"],
        customer_id=row["customer_id"],
        location_id=row["location_id"],
        label=row["label"],
        address_line1=row["address_line1"],
        address_line2=row["address_line2"],
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        country=row["country"],
        is_primary=bool(row["is_primary"]),
        is_active=bool(row["is_active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_supplier_location(row: Row) -> SupplierLocation:
    return SupplierLocation(
        id=row["id"],
        supplier_id=row["supplier_id"],
        location_id=row["location_id"],
        label=row["label"],
        address_line1=row["address_line1"],
        address_line2=row["address_line2"],
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        country=row["country"],
        is_primary=bool(row["is_primary"]),
        is_active=bool(row["is_active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_location(row: Row) -> Location:
    assigned_customer_count = row["assigned_customer_count"]
    assigned_supplier_count = row["assigned_supplier_count"]
    assigned_names = ", ".join(
        name for name in (row["assigned_customer_names"], row["assigned_supplier_names"]) if name
    ) or None

    return Location(
        id=row["id"],
        address_line1=row["address_line1"],
        address_line2=row["address_line2"],
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        country=row["country"],
        assigned_customer_count=assigned_customer_count,
        assigned_customer_names=row["assigned_customer_names"],
        assigned_supplier_count=assigned_supplier_count,
        assigned_supplier_names=row["assigned_supplier_names"],
        assigned_count=assigned_customer_count + assigned_supplier_count,
        assigned_names=assigned_names,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_location_customer_assignment(row: Row) -> LocationCustomerAssignment:
    return LocationCustomerAssignment(
        id=row["id"],
        customer_id=row["customer_id"],
        customer_name=row["customer_name"],
        customer_email=row["customer_email"],
        label=row["label"],
        is_primary=bool(row["is_primary"]),
        is_active=bool(row["is_active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_location_supplier_assignment(row: Row) -> LocationSupplierAssignment:
    return LocationSupplierAssignment(
        id=row["id"],
        supplier_id=row["supplier_id"],
        supplier_name=row["supplier_name"],
        supplier_phone=row["supplier_phone"],
        supplier_email=row["supplier_email"],
        label=row["label"],
        is_primary=bool(row["is_primary"]),
        is_active=bool(row["is_active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_location_invoice(row: Row) -> LocationInvoice:
    return LocationInvoice(
        id=row["id"],
        customer_id=row["customer_id"],
        customer_name=row["customer_name"],
        customer_location_id=row["customer_location_id"],
        date_issued=row["date_issued"],
        date_due=row["date_due"],
        total=row["total"],
        status=row["status"],
    )


def _select_customer_location_sql(where_clause: str) -> str:
    return f"""
        SELECT
            cl.id,
            cl.customer_id,
            cl.location_id,
            cl.label,
            l.address_line1,
            l.address_line2,
            l.city,
            l.state,
            l.postal_code,
            l.country,
            cl.is_primary,
            cl.is_active,
            cl.notes,
            cl.created_at,
            cl.updated_at
        FROM customer_locations cl
        JOIN locations l ON l.id = cl.location_id
        WHERE {where_clause}
    """


def _select_supplier_location_sql(where_clause: str) -> str:
    return f"""
        SELECT
            sl.id,
            sl.supplier_id,
            sl.location_id,
            sl.label,
            l.address_line1,
            l.address_line2,
            l.city,
            l.state,
            l.postal_code,
            l.country,
            sl.is_primary,
            sl.is_active,
            sl.notes,
            sl.created_at,
            sl.updated_at
        FROM supplier_locations sl
        JOIN locations l ON l.id = sl.location_id
        WHERE {where_clause}
    """


def _clear_primary_for_customer(cursor, customer_id: int) -> None:
    cursor.execute(
        """
        UPDATE customer_locations
        SET is_primary = 0
        WHERE customer_id = ?
        """,
        (customer_id,),
    )


def _clear_primary_for_supplier(cursor, supplier_id: int) -> None:
    cursor.execute(
        """
        UPDATE supplier_locations
        SET is_primary = 0
        WHERE supplier_id = ?
        """,
        (supplier_id,),
    )


def _get_location_id_by_address(
    cursor,
    *,
    address_line1: str,
    address_line2: str | None,
    city: str,
    state: str,
    postal_code: str,
    country: str,
) -> int | None:
    row = cursor.execute(
        """
        SELECT id
        FROM locations
        WHERE lower(trim(address_line1)) = lower(trim(?))
            AND lower(trim(COALESCE(address_line2, ''))) = lower(trim(COALESCE(?, '')))
            AND lower(trim(city)) = lower(trim(?))
            AND lower(trim(state)) = lower(trim(?))
            AND lower(trim(postal_code)) = lower(trim(?))
            AND lower(trim(country)) = lower(trim(?))
        """,
        (address_line1, address_line2, city, state, postal_code, country),
    ).fetchone()
    return row["id"] if row else None


def _get_or_create_location(
    cursor,
    *,
    address_line1: str,
    address_line2: str | None,
    city: str,
    state: str,
    postal_code: str,
    country: str,
) -> int:
    location_id = _get_location_id_by_address(
        cursor,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )
    if location_id is not None:
        return location_id

    cursor.execute(
        """
        INSERT INTO locations (
            address_line1,
            address_line2,
            city,
            state,
            postal_code,
            country
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (address_line1, address_line2, city, state, postal_code, country),
    )
    return cursor.lastrowid


def _get_customer_location_id_for_location(
    cursor,
    customer_id: int,
    location_id: int,
    exclude_customer_location_id: int | None = None,
) -> int | None:
    sql = "SELECT id FROM customer_locations WHERE customer_id = ? AND location_id = ?"
    params = [customer_id, location_id]
    if exclude_customer_location_id is not None:
        sql += " AND id != ?"
        params.append(exclude_customer_location_id)
    row = cursor.execute(sql, params).fetchone()
    return row["id"] if row else None


def _get_supplier_location_id_for_location(
    cursor,
    supplier_id: int,
    location_id: int,
    exclude_supplier_location_id: int | None = None,
) -> int | None:
    sql = "SELECT id FROM supplier_locations WHERE supplier_id = ? AND location_id = ?"
    params = [supplier_id, location_id]
    if exclude_supplier_location_id is not None:
        sql += " AND id != ?"
        params.append(exclude_supplier_location_id)
    row = cursor.execute(sql, params).fetchone()
    return row["id"] if row else None


def customer_has_locations(cursor, customer_id: int) -> bool:
    row = cursor.execute(
        "SELECT 1 FROM customer_locations WHERE customer_id = ? LIMIT 1",
        (customer_id,),
    ).fetchone()
    return row is not None


def supplier_has_locations(cursor, supplier_id: int) -> bool:
    row = cursor.execute(
        "SELECT 1 FROM supplier_locations WHERE supplier_id = ? LIMIT 1",
        (supplier_id,),
    ).fetchone()
    return row is not None


def assert_supplier_exists(cursor, supplier_id: int) -> None:
    if get_supplier_by_id(cursor, supplier_id) is None:
        raise ValueError(f"Supplier not found (id={supplier_id}).")


def get_locations(cursor) -> list[Location]:
    cursor.execute(
        """
        SELECT
            l.id,
            l.address_line1,
            l.address_line2,
            l.city,
            l.state,
            l.postal_code,
            l.country,
            (
                SELECT COUNT(*)
                FROM customer_locations cl
                WHERE cl.location_id = l.id
            ) AS assigned_customer_count,
            (
                SELECT GROUP_CONCAT(name, ', ')
                FROM (
                    SELECT c.name AS name
                    FROM customer_locations cl
                    JOIN customers c ON c.id = cl.customer_id
                    WHERE cl.location_id = l.id
                    ORDER BY lower(c.name), c.id
                )
            ) AS assigned_customer_names,
            (
                SELECT COUNT(*)
                FROM supplier_locations sl
                WHERE sl.location_id = l.id
            ) AS assigned_supplier_count,
            (
                SELECT GROUP_CONCAT(name, ', ')
                FROM (
                    SELECT s.name AS name
                    FROM supplier_locations sl
                    JOIN suppliers s ON s.id = sl.supplier_id
                    WHERE sl.location_id = l.id
                    ORDER BY lower(s.name), s.id
                )
            ) AS assigned_supplier_names,
            l.created_at,
            l.updated_at
        FROM locations l
        ORDER BY lower(l.city), lower(l.address_line1), l.id
        """
    )
    return [_to_location(row) for row in cursor.fetchall()]


def create_location(cursor, location: LocationCreate) -> Location:
    address_line1 = _normalize_required_text(location.address_line1, "Address line 1")
    address_line2 = normalize_optional_customer_text(location.address_line2)
    city = _normalize_required_text(location.city, "City")
    state = _normalize_required_text(location.state, "State")
    postal_code = _normalize_required_text(location.postal_code, "Postal code")
    country = _normalize_required_text(location.country, "Country")

    existing_location_id = _get_location_id_by_address(
        cursor,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )
    if existing_location_id is not None:
        raise ValueError("That location already exists.")

    cursor.execute(
        """
        INSERT INTO locations (
            address_line1,
            address_line2,
            city,
            state,
            postal_code,
            country
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (address_line1, address_line2, city, state, postal_code, country),
    )

    created_location = get_location_by_id(cursor, cursor.lastrowid)
    if created_location is None:
        raise RuntimeError("Location was created but could not be retrieved.")

    return created_location


def get_location_by_id(cursor, location_id: int) -> Location | None:
    cursor.execute(
        """
        SELECT
            l.id,
            l.address_line1,
            l.address_line2,
            l.city,
            l.state,
            l.postal_code,
            l.country,
            (
                SELECT COUNT(*)
                FROM customer_locations cl
                WHERE cl.location_id = l.id
            ) AS assigned_customer_count,
            (
                SELECT GROUP_CONCAT(name, ', ')
                FROM (
                    SELECT c.name AS name
                    FROM customer_locations cl
                    JOIN customers c ON c.id = cl.customer_id
                    WHERE cl.location_id = l.id
                    ORDER BY lower(c.name), c.id
                )
            ) AS assigned_customer_names,
            (
                SELECT COUNT(*)
                FROM supplier_locations sl
                WHERE sl.location_id = l.id
            ) AS assigned_supplier_count,
            (
                SELECT GROUP_CONCAT(name, ', ')
                FROM (
                    SELECT s.name AS name
                    FROM supplier_locations sl
                    JOIN suppliers s ON s.id = sl.supplier_id
                    WHERE sl.location_id = l.id
                    ORDER BY lower(s.name), s.id
                )
            ) AS assigned_supplier_names,
            l.created_at,
            l.updated_at
        FROM locations l
        WHERE l.id = ?
        """,
        (location_id,),
    )
    row = cursor.fetchone()
    return _to_location(row) if row else None


def update_location(
    cursor,
    location_id: int,
    *,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
) -> Location | None:
    location = get_location_by_id(cursor, location_id)
    if location is None:
        return None

    next_address_line1 = location.address_line1
    next_address_line2 = location.address_line2
    next_city = location.city
    next_state = location.state
    next_postal_code = location.postal_code
    next_country = location.country

    if address_line1 is not None:
        next_address_line1 = _normalize_required_text(address_line1, "Address line 1")
    if address_line2 is not None:
        next_address_line2 = normalize_optional_customer_text(address_line2)
    if city is not None:
        next_city = _normalize_required_text(city, "City")
    if state is not None:
        next_state = _normalize_required_text(state, "State")
    if postal_code is not None:
        next_postal_code = _normalize_required_text(postal_code, "Postal code")
    if country is not None:
        next_country = _normalize_required_text(country, "Country")

    existing_location_id = _get_location_id_by_address(
        cursor,
        address_line1=next_address_line1,
        address_line2=next_address_line2,
        city=next_city,
        state=next_state,
        postal_code=next_postal_code,
        country=next_country,
    )
    if existing_location_id is not None and existing_location_id != location_id:
        raise ValueError("That location already exists.")

    cursor.execute(
        """
        UPDATE locations
        SET
            address_line1 = ?,
            address_line2 = ?,
            city = ?,
            state = ?,
            postal_code = ?,
            country = ?
        WHERE id = ?
        """,
        (
            next_address_line1,
            next_address_line2,
            next_city,
            next_state,
            next_postal_code,
            next_country,
            location_id,
        ),
    )
    return get_location_by_id(cursor, location_id)


def get_location_customer_assignments(cursor, location_id: int) -> list[LocationCustomerAssignment]:
    cursor.execute(
        """
        SELECT
            cl.id,
            cl.customer_id,
            c.name AS customer_name,
            c.email AS customer_email,
            cl.label,
            cl.is_primary,
            cl.is_active,
            cl.notes,
            cl.created_at,
            cl.updated_at
        FROM customer_locations cl
        JOIN customers c ON c.id = cl.customer_id
        WHERE cl.location_id = ?
        ORDER BY cl.is_active DESC, cl.is_primary DESC, lower(c.name), cl.id
        """,
        (location_id,),
    )
    return [_to_location_customer_assignment(row) for row in cursor.fetchall()]


def get_location_supplier_assignments(cursor, location_id: int) -> list[LocationSupplierAssignment]:
    cursor.execute(
        """
        SELECT
            sl.id,
            sl.supplier_id,
            s.name AS supplier_name,
            s.phone AS supplier_phone,
            s.email AS supplier_email,
            sl.label,
            sl.is_primary,
            sl.is_active,
            sl.notes,
            sl.created_at,
            sl.updated_at
        FROM supplier_locations sl
        JOIN suppliers s ON s.id = sl.supplier_id
        WHERE sl.location_id = ?
        ORDER BY sl.is_active DESC, sl.is_primary DESC, lower(s.name), sl.id
        """,
        (location_id,),
    )
    return [_to_location_supplier_assignment(row) for row in cursor.fetchall()]


def get_location_invoices(cursor, location_id: int) -> list[LocationInvoice]:
    cursor.execute(
        """
        SELECT
            i.id,
            i.customer_id,
            c.name AS customer_name,
            i.location_id AS customer_location_id,
            i.date_issued,
            i.date_due,
            i.total,
            i.status
        FROM invoices i
        JOIN customer_locations cl ON cl.id = i.location_id
        JOIN customers c ON c.id = i.customer_id
        WHERE cl.location_id = ?
        ORDER BY COALESCE(i.date_issued, ''), i.id
        """,
        (location_id,),
    )
    return [_to_location_invoice(row) for row in cursor.fetchall()]


def create_customer_location(cursor, location: CustomerLocationCreate) -> CustomerLocation:
    validate_positive_id(location.customer_id, "Customer id")
    assert_customer_exists(cursor, location.customer_id)

    label = _normalize_required_text(location.label, "Location label")
    address_line1 = _normalize_required_text(location.address_line1, "Address line 1")
    address_line2 = normalize_optional_customer_text(location.address_line2)
    city = _normalize_required_text(location.city, "City")
    state = _normalize_required_text(location.state, "State")
    postal_code = _normalize_required_text(location.postal_code, "Postal code")
    country = _normalize_required_text(location.country, "Country")
    is_primary = normalize_is_active(location.is_primary)
    is_active = normalize_is_active(location.is_active)
    notes = normalize_optional_customer_text(location.notes)

    location_id = _get_or_create_location(
        cursor,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )
    if _get_customer_location_id_for_location(cursor, location.customer_id, location_id) is not None:
        raise ValueError("That address is already assigned to this customer.")

    if not customer_has_locations(cursor, location.customer_id):
        is_primary = 1

    if is_primary and is_active:
        _clear_primary_for_customer(cursor, location.customer_id)

    cursor.execute(
        """
        INSERT INTO customer_locations (
            customer_id,
            location_id,
            label,
            is_primary,
            is_active,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            location.customer_id,
            location_id,
            label,
            is_primary,
            is_active,
            notes,
        ),
    )

    created_location = get_customer_location_by_id(cursor, cursor.lastrowid)
    if created_location is None:
        raise RuntimeError("Customer location was created but could not be retrieved.")

    return created_location


def create_supplier_location(cursor, location: SupplierLocationCreate) -> SupplierLocation:
    validate_positive_id(location.supplier_id, "Supplier id")
    assert_supplier_exists(cursor, location.supplier_id)

    label = _normalize_required_text(location.label, "Location label")
    address_line1 = _normalize_required_text(location.address_line1, "Address line 1")
    address_line2 = normalize_optional_customer_text(location.address_line2)
    city = _normalize_required_text(location.city, "City")
    state = _normalize_required_text(location.state, "State")
    postal_code = _normalize_required_text(location.postal_code, "Postal code")
    country = _normalize_required_text(location.country, "Country")
    is_primary = normalize_is_active(location.is_primary)
    is_active = normalize_is_active(location.is_active)
    notes = normalize_optional_customer_text(location.notes)

    location_id = _get_or_create_location(
        cursor,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )
    if _get_supplier_location_id_for_location(cursor, location.supplier_id, location_id) is not None:
        raise ValueError("That address is already assigned to this supplier.")

    if not supplier_has_locations(cursor, location.supplier_id):
        is_primary = 1

    if is_primary and is_active:
        _clear_primary_for_supplier(cursor, location.supplier_id)

    cursor.execute(
        """
        INSERT INTO supplier_locations (
            supplier_id,
            location_id,
            label,
            is_primary,
            is_active,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            location.supplier_id,
            location_id,
            label,
            is_primary,
            is_active,
            notes,
        ),
    )

    created_location = get_supplier_location_by_id(cursor, cursor.lastrowid)
    if created_location is None:
        raise RuntimeError("Supplier location was created but could not be retrieved.")

    return created_location


def get_customer_location_by_id(cursor, location_id: int) -> CustomerLocation | None:
    cursor.execute(_select_customer_location_sql("cl.id = ?"), (location_id,))
    row = cursor.fetchone()
    return _to_customer_location(row) if row else None


def get_supplier_location_by_id(cursor, location_id: int) -> SupplierLocation | None:
    cursor.execute(_select_supplier_location_sql("sl.id = ?"), (location_id,))
    row = cursor.fetchone()
    return _to_supplier_location(row) if row else None


def get_customer_locations(
    cursor,
    customer_id: int,
    active_only: bool = False,
) -> list[CustomerLocation]:
    sql = _select_customer_location_sql("cl.customer_id = ?")
    params = [customer_id]

    if active_only:
        sql += " AND cl.is_active = ?"
        params.append(1)

    sql += " ORDER BY cl.is_primary DESC, cl.id"
    cursor.execute(sql, params)
    return [_to_customer_location(row) for row in cursor.fetchall()]


def get_supplier_locations(
    cursor,
    supplier_id: int,
    active_only: bool = False,
) -> list[SupplierLocation]:
    sql = _select_supplier_location_sql("sl.supplier_id = ?")
    params = [supplier_id]

    if active_only:
        sql += " AND sl.is_active = ?"
        params.append(1)

    sql += " ORDER BY sl.is_primary DESC, sl.id"
    cursor.execute(sql, params)
    return [_to_supplier_location(row) for row in cursor.fetchall()]


def location_belongs_to_customer(cursor, location_id: int, customer_id: int) -> bool:
    row = cursor.execute(
        """
        SELECT 1
        FROM customer_locations
        WHERE id = ? AND customer_id = ?
        """,
        (location_id, customer_id),
    ).fetchone()
    return row is not None


def location_belongs_to_supplier(cursor, location_id: int, supplier_id: int) -> bool:
    row = cursor.execute(
        """
        SELECT 1
        FROM supplier_locations
        WHERE id = ? AND supplier_id = ?
        """,
        (location_id, supplier_id),
    ).fetchone()
    return row is not None


def update_customer_location(
    cursor,
    location_id: int,
    *,
    label: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    is_primary: bool | None = None,
    is_active: bool | None = None,
    notes: str | None = None,
) -> CustomerLocation | None:
    location = get_customer_location_by_id(cursor, location_id)
    if location is None:
        return None

    customer_updates, customer_params = [], []
    next_is_active = location.is_active
    next_is_primary = location.is_primary

    next_address_line1 = location.address_line1
    next_address_line2 = location.address_line2
    next_city = location.city
    next_state = location.state
    next_postal_code = location.postal_code
    next_country = location.country
    should_update_address = False

    if label is not None:
        customer_updates.append("label = ?")
        customer_params.append(_normalize_required_text(label, "Location label"))
    if address_line1 is not None:
        next_address_line1 = _normalize_required_text(address_line1, "Address line 1")
        should_update_address = True
    if address_line2 is not None:
        next_address_line2 = normalize_optional_customer_text(address_line2)
        should_update_address = True
    if city is not None:
        next_city = _normalize_required_text(city, "City")
        should_update_address = True
    if state is not None:
        next_state = _normalize_required_text(state, "State")
        should_update_address = True
    if postal_code is not None:
        next_postal_code = _normalize_required_text(postal_code, "Postal code")
        should_update_address = True
    if country is not None:
        next_country = _normalize_required_text(country, "Country")
        should_update_address = True
    if is_primary is not None:
        next_is_primary = bool(is_primary)
        customer_updates.append("is_primary = ?")
        customer_params.append(normalize_is_active(is_primary))
    if is_active is not None:
        next_is_active = bool(is_active)
        customer_updates.append("is_active = ?")
        customer_params.append(normalize_is_active(is_active))
    if notes is not None:
        customer_updates.append("notes = ?")
        customer_params.append(normalize_optional_customer_text(notes))

    if should_update_address:
        next_location_id = _get_or_create_location(
            cursor,
            address_line1=next_address_line1,
            address_line2=next_address_line2,
            city=next_city,
            state=next_state,
            postal_code=next_postal_code,
            country=next_country,
        )
        if _get_customer_location_id_for_location(
            cursor,
            location.customer_id,
            next_location_id,
            exclude_customer_location_id=location.id,
        ) is not None:
            raise ValueError("That address is already assigned to this customer.")
        customer_updates.append("location_id = ?")
        customer_params.append(next_location_id)

    if not customer_updates:
        return location

    if next_is_primary and next_is_active:
        _clear_primary_for_customer(cursor, location.customer_id)

    customer_params.append(location_id)
    query = f"UPDATE customer_locations SET {', '.join(customer_updates)} WHERE id = ?"
    cursor.execute(query, tuple(customer_params))
    return get_customer_location_by_id(cursor, location_id)


def update_supplier_location(
    cursor,
    location_id: int,
    *,
    label: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    is_primary: bool | None = None,
    is_active: bool | None = None,
    notes: str | None = None,
) -> SupplierLocation | None:
    location = get_supplier_location_by_id(cursor, location_id)
    if location is None:
        return None

    supplier_updates, supplier_params = [], []
    next_is_active = location.is_active
    next_is_primary = location.is_primary

    next_address_line1 = location.address_line1
    next_address_line2 = location.address_line2
    next_city = location.city
    next_state = location.state
    next_postal_code = location.postal_code
    next_country = location.country
    should_update_address = False

    if label is not None:
        supplier_updates.append("label = ?")
        supplier_params.append(_normalize_required_text(label, "Location label"))
    if address_line1 is not None:
        next_address_line1 = _normalize_required_text(address_line1, "Address line 1")
        should_update_address = True
    if address_line2 is not None:
        next_address_line2 = normalize_optional_customer_text(address_line2)
        should_update_address = True
    if city is not None:
        next_city = _normalize_required_text(city, "City")
        should_update_address = True
    if state is not None:
        next_state = _normalize_required_text(state, "State")
        should_update_address = True
    if postal_code is not None:
        next_postal_code = _normalize_required_text(postal_code, "Postal code")
        should_update_address = True
    if country is not None:
        next_country = _normalize_required_text(country, "Country")
        should_update_address = True
    if is_primary is not None:
        next_is_primary = bool(is_primary)
        supplier_updates.append("is_primary = ?")
        supplier_params.append(normalize_is_active(is_primary))
    if is_active is not None:
        next_is_active = bool(is_active)
        supplier_updates.append("is_active = ?")
        supplier_params.append(normalize_is_active(is_active))
    if notes is not None:
        supplier_updates.append("notes = ?")
        supplier_params.append(normalize_optional_customer_text(notes))

    if should_update_address:
        next_location_id = _get_or_create_location(
            cursor,
            address_line1=next_address_line1,
            address_line2=next_address_line2,
            city=next_city,
            state=next_state,
            postal_code=next_postal_code,
            country=next_country,
        )
        if _get_supplier_location_id_for_location(
            cursor,
            location.supplier_id,
            next_location_id,
            exclude_supplier_location_id=location.id,
        ) is not None:
            raise ValueError("That address is already assigned to this supplier.")
        supplier_updates.append("location_id = ?")
        supplier_params.append(next_location_id)

    if not supplier_updates:
        return location

    if next_is_primary and next_is_active:
        _clear_primary_for_supplier(cursor, location.supplier_id)

    supplier_params.append(location_id)
    query = f"UPDATE supplier_locations SET {', '.join(supplier_updates)} WHERE id = ?"
    cursor.execute(query, tuple(supplier_params))
    return get_supplier_location_by_id(cursor, location_id)


def delete_customer_location(cursor, location_id: int) -> bool:
    cursor.execute("DELETE FROM customer_locations WHERE id = ?", (location_id,))
    return cursor.rowcount > 0


def delete_supplier_location(cursor, location_id: int) -> bool:
    cursor.execute("DELETE FROM supplier_locations WHERE id = ?", (location_id,))
    return cursor.rowcount > 0
