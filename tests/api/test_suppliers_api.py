INVALID_ID = 9999


def create_supplier(api_client, name="Johnstone", **overrides):
    payload = {
        "name": name,
        "phone": "555-0100",
        "email": "source@example.com",
        "website": "https://example.com",
    }
    payload.update(overrides)

    response = api_client.post("/api/suppliers/", payload, format="json")
    assert response.status_code == 201, response.json()
    return response.json()


def test_list_suppliers_returns_200(api_client, test_db):
    response = api_client.get("/api/suppliers/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_supplier_returns_201(api_client, test_db):
    response = api_client.post(
        "/api/suppliers/",
        {
            "name": "Johnstone",
            "phone": "555-0100",
            "email": "source@example.com",
            "website": "https://example.com",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Johnstone"
    assert data["phone"] == "555-0100"
    assert data["email"] == "source@example.com"
    assert data["website"] == "https://example.com"
    assert data["is_active"] is True


def test_create_duplicate_supplier_returns_clear_400(api_client, test_db):
    create_supplier(api_client, name="Johnstone")

    response = api_client.post(
        "/api/suppliers/",
        {"name": "johnstone"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == 'A supplier named "Johnstone" already exists.'


def test_get_supplier_returns_200(api_client, test_db):
    supplier = create_supplier(api_client)

    response = api_client.get(f"/api/suppliers/{supplier['id']}/")

    assert response.status_code == 200
    assert response.json()["name"] == "Johnstone"


def test_patch_supplier_returns_200(api_client, test_db):
    supplier = create_supplier(api_client)

    response = api_client.patch(
        f"/api/suppliers/{supplier['id']}/",
        {
            "name": "Home Depot",
            "website": "https://homedepot.example.com",
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Home Depot"
    assert data["website"] == "https://homedepot.example.com"


def test_deactivate_supplier_returns_200(api_client, test_db):
    supplier = create_supplier(api_client)

    response = api_client.patch(f"/api/suppliers/{supplier['id']}/deactivate/")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_list_suppliers_active_only_returns_active_suppliers(api_client, test_db):
    create_supplier(api_client, name="Active", is_active=True)
    create_supplier(api_client, name="Inactive", is_active=False)

    response = api_client.get("/api/suppliers/?active_only=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active"


def test_delete_unused_supplier_returns_204(api_client, test_db):
    supplier = create_supplier(api_client)

    response = api_client.delete(f"/api/suppliers/{supplier['id']}/")

    assert response.status_code == 204


def test_delete_missing_supplier_returns_404(api_client, test_db):
    response = api_client.delete(f"/api/suppliers/{INVALID_ID}/")

    assert response.status_code == 404


def test_add_supplier_to_product_returns_201(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)

    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {
            "supplier_id": supplier["id"],
            "note": "Counter pickup",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product_id
    assert data["supplier_id"] == supplier["id"]
    assert data["note"] == "Counter pickup"


def test_list_product_suppliers_returns_suppliers(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.get(f"/api/products/{product_id}/suppliers/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Johnstone"


def test_add_duplicate_supplier_to_product_returns_409(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    first_response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert first_response.status_code == 201

    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == f'Supplier "Johnstone" is already attached to product {product_id}.'


def test_add_inactive_supplier_to_product_returns_400(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client, is_active=False)

    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive suppliers cannot be added to products."


def test_patch_product_supplier_note_returns_200(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.patch(
        f"/api/products/{product_id}/suppliers/{supplier['id']}/",
        {"note": "Usually stocked"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["note"] == "Usually stocked"


def test_supplier_products_returns_products(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.get(f"/api/suppliers/{supplier['id']}/products/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == product_id
    assert data[0]["name"] == "Widget"


def test_delete_supplier_with_product_returns_409(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.delete(f"/api/suppliers/{supplier['id']}/")

    assert response.status_code == 409
    assert response.json()["detail"] == 'Cannot delete supplier "Johnstone" because 1 product uses it.'


def test_remove_supplier_from_product_returns_204(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.delete(f"/api/products/{product_id}/suppliers/{supplier['id']}/")

    assert response.status_code == 204


def test_remove_inactive_supplier_from_all_products(api_client, test_db, post_product):
    product_id = post_product().json()["id"]
    supplier = create_supplier(api_client)
    response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier["id"]},
        format="json",
    )
    assert response.status_code == 201
    deactivate_response = api_client.patch(f"/api/suppliers/{supplier['id']}/deactivate/")
    assert deactivate_response.status_code == 200

    response = api_client.post(f"/api/suppliers/{supplier['id']}/remove-from-products/")

    assert response.status_code == 200
    assert response.json() == {
        "supplier_id": supplier["id"],
        "removed_count": 1,
    }


def test_remove_active_supplier_from_all_products_returns_400(api_client, test_db):
    supplier = create_supplier(api_client)

    response = api_client.post(f"/api/suppliers/{supplier['id']}/remove-from-products/")

    assert response.status_code == 400
    assert response.json()["detail"] == "Only inactive suppliers can be removed from all products."
