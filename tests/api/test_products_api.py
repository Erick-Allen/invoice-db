INVALID_ID = 9999


def test_list_products_returns_200(api_client, test_db):
    response = api_client.get("/api/products/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_product_returns_201(api_client, test_db):
    response = api_client.post(
        "/api/products/",
        {
            "name": "Widget",
            "description": "A test widget",
            "unit_price_cents": 1234,
            "is_active": True,
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Widget"
    assert data["description"] == "A test widget"
    assert data["unit_price_cents"] == 1234
    assert data["is_active"] is True


def test_get_product_returns_200(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.get(f"/api/products/{product_id}/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "Widget"


def test_patch_product_with_single_field_returns_200(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.patch(
        f"/api/products/{product_id}/",
        {"unit_price_cents": 2500},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["unit_price_cents"] == 2500


def test_patch_product_with_multiple_fields_returns_200(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.patch(
        f"/api/products/{product_id}/",
        {
            "name": "Updated Widget",
            "description": "Updated description",
            "is_active": False,
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Widget"
    assert data["description"] == "Updated description"
    assert data["is_active"] is False


def test_deactivate_product_returns_200(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.patch(f"/api/products/{product_id}/deactivate/")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_list_products_active_only_returns_active_products(api_client, test_db, post_product):
    post_product(name="Active Widget", is_active=True)
    post_product(name="Inactive Widget", is_active=False)

    response = api_client.get("/api/products/?active_only=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active Widget"


def test_delete_product_returns_204(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.delete(f"/api/products/{product_id}/")

    assert response.status_code == 204


def test_create_product_with_blank_name_returns_400(api_client, test_db):
    response = api_client.post(
        "/api/products/",
        {
            "name": " ",
            "unit_price_cents": 1234,
        },
        format="json",
    )

    assert response.status_code == 400


def test_create_product_with_negative_price_returns_400(api_client, test_db):
    response = api_client.post(
        "/api/products/",
        {
            "name": "Widget",
            "unit_price_cents": -1,
        },
        format="json",
    )

    assert response.status_code == 400


def test_get_missing_product_returns_404(api_client, test_db):
    response = api_client.get(f"/api/products/{INVALID_ID}/")

    assert response.status_code == 404


def test_patch_product_with_empty_body_returns_400(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]

    response = api_client.patch(
        f"/api/products/{product_id}/",
        {},
        format="json",
    )

    assert response.status_code == 400


def test_patch_missing_product_returns_404(api_client, test_db):
    response = api_client.patch(
        f"/api/products/{INVALID_ID}/",
        {"name": "Missing"},
        format="json",
    )

    assert response.status_code == 404


def test_delete_missing_product_returns_404(api_client, test_db):
    response = api_client.delete(f"/api/products/{INVALID_ID}/")

    assert response.status_code == 404
