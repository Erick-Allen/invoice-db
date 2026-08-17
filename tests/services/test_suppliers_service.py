import pytest

from invoice_db.services import exceptions
from invoice_db.services import products as product_services
from invoice_db.services import suppliers as supplier_services


def create_product(cursor, name="Widget"):
    return product_services.create_product(
        cursor,
        name=name,
        cost_cents=1000,
        unit_price_cents=2500,
    )


def test_create_and_list_suppliers(cursor):
    supplier = supplier_services.create_supplier(
        cursor,
        name=" Johnstone ",
        phone=" 555-0100 ",
        email=" source@example.com ",
        website=" https://example.com ",
    )

    result = supplier_services.list_suppliers(cursor)

    assert supplier["name"] == "Johnstone"
    assert supplier["phone"] == "555-0100"
    assert supplier["email"] == "source@example.com"
    assert supplier["website"] == "https://example.com"
    assert supplier["id"] in {existing_supplier["id"] for existing_supplier in result}


def test_create_duplicate_supplier_raises_clear_validation_error(cursor):
    supplier_services.create_supplier(cursor, name="Johnstone")

    with pytest.raises(exceptions.ValidationError, match='A supplier named "Johnstone" already exists.'):
        supplier_services.create_supplier(cursor, name="johnstone")


def test_update_supplier_duplicate_name_raises_clear_validation_error(cursor):
    supplier_services.create_supplier(cursor, name="Johnstone")
    supplier = supplier_services.create_supplier(cursor, name="Home Depot")

    with pytest.raises(exceptions.ValidationError, match='A supplier named "Johnstone" already exists.'):
        supplier_services.update_supplier_by_id(cursor, supplier["id"], name="johnstone")


def test_deactivate_supplier(cursor):
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")

    updated = supplier_services.deactivate_supplier(cursor, supplier["id"])

    assert updated["is_active"] is False


def test_list_suppliers_active_only(cursor):
    active = supplier_services.create_supplier(cursor, name="Johnstone")
    inactive = supplier_services.create_supplier(cursor, name="Archived", is_active=False)

    result = supplier_services.list_suppliers(cursor, active_only=True)

    assert active["id"] in {supplier["id"] for supplier in result}
    assert inactive["id"] not in {supplier["id"] for supplier in result}


def test_delete_unused_supplier(cursor):
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")

    supplier_services.delete_supplier(cursor, supplier["id"])

    with pytest.raises(exceptions.NotFoundError):
        supplier_services.get_supplier_by_id(cursor, supplier["id"])


def test_delete_supplier_with_products_raises_conflict(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])

    with pytest.raises(exceptions.ConflictError, match='Cannot delete supplier "Johnstone" because 1 product uses it.'):
        supplier_services.delete_supplier(cursor, supplier["id"])


def test_add_supplier_to_product(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")

    product_supplier = supplier_services.add_supplier_to_product(
        cursor,
        product["id"],
        supplier["id"],
        note="Usually stocked",
    )
    result = supplier_services.list_product_suppliers(cursor, product["id"])

    assert product_supplier["product_id"] == product["id"]
    assert product_supplier["supplier_id"] == supplier["id"]
    assert product_supplier["note"] == "Usually stocked"
    assert [supplier["name"] for supplier in result] == ["Johnstone"]


def test_add_supplier_to_product_rejects_inactive_supplier(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone", is_active=False)

    with pytest.raises(exceptions.ValidationError, match="Inactive suppliers cannot be added to products."):
        supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])


def test_add_supplier_to_product_rejects_duplicate_assignment(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])

    with pytest.raises(exceptions.ConflictError, match='Supplier "Johnstone" is already attached to product'):
        supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])


def test_list_supplier_products(cursor):
    product = create_product(cursor, name="Widget")
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])

    result = supplier_services.list_supplier_products(cursor, supplier["id"])

    assert [product["name"] for product in result] == ["Widget"]


def test_update_product_supplier_note(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])

    updated = supplier_services.update_product_supplier_note(
        cursor,
        product["id"],
        supplier["id"],
        "Counter pickup",
    )

    assert updated["note"] == "Counter pickup"


def test_remove_supplier_from_product(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, product["id"], supplier["id"])

    supplier_services.remove_supplier_from_product(cursor, product["id"], supplier["id"])

    assert supplier_services.list_product_suppliers(cursor, product["id"]) == []


def test_remove_missing_supplier_assignment_raises_not_found(cursor):
    product = create_product(cursor)
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")

    with pytest.raises(exceptions.NotFoundError):
        supplier_services.remove_supplier_from_product(cursor, product["id"], supplier["id"])


def test_remove_supplier_from_all_products_requires_inactive_supplier(cursor):
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")

    with pytest.raises(exceptions.ValidationError, match="Only inactive suppliers can be removed from all products."):
        supplier_services.remove_supplier_from_all_products(cursor, supplier["id"])


def test_remove_inactive_supplier_from_all_products(cursor):
    first = create_product(cursor, name="Widget")
    second = create_product(cursor, name="Cable")
    supplier = supplier_services.create_supplier(cursor, name="Johnstone")
    supplier_services.add_supplier_to_product(cursor, first["id"], supplier["id"])
    supplier_services.add_supplier_to_product(cursor, second["id"], supplier["id"])
    supplier_services.deactivate_supplier(cursor, supplier["id"])

    result = supplier_services.remove_supplier_from_all_products(cursor, supplier["id"])

    assert result == {
        "supplier_id": supplier["id"],
        "removed_count": 2,
    }
    supplier_services.delete_supplier(cursor, supplier["id"])
