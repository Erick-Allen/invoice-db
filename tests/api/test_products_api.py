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
            "cost_cents": 900,
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
    assert data["cost_cents"] == 900
    assert data["unit_price_cents"] == 1234
    assert data["category_id"] == 1
    assert data["category_name"] == "Uncategorized"
    assert data["is_active"] is True
    assert data["product_supplier_count"] == 0
    assert data["invoice_item_count"] == 0


def test_create_product_with_category_returns_201(api_client, test_db):
    category_response = api_client.post(
        "/api/product-categories/",
        {
            "name": "Labor",
            "description": "Billable work",
        },
        format="json",
    )
    category_id = category_response.json()["id"]

    response = api_client.post(
        "/api/products/",
        {
            "name": "Consulting",
            "unit_price_cents": 12500,
            "category_id": category_id,
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category_id"] == category_id
    assert data["category_name"] == "Labor"


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
        {"cost_cents": 1200, "unit_price_cents": 2500},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["cost_cents"] == 1200
    assert data["unit_price_cents"] == 2500


def test_patch_product_category_returns_200(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    category_id = category_response.json()["id"]

    response = api_client.patch(
        f"/api/products/{product_id}/",
        {"category_id": category_id},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == category_id
    assert data["category_name"] == "Materials"


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


def test_delete_product_with_relationships_returns_409(api_client, test_db, post_product):
    product_response = post_product()
    product_id = product_response.json()["id"]
    supplier_response = api_client.post(
        "/api/suppliers/",
        {"name": "Johnstone"},
        format="json",
    )
    supplier_id = supplier_response.json()["id"]
    attach_response = api_client.post(
        f"/api/products/{product_id}/suppliers/",
        {"supplier_id": supplier_id},
        format="json",
    )
    assert attach_response.status_code == 201

    product_detail_response = api_client.get(f"/api/products/{product_id}/")
    assert product_detail_response.json()["product_supplier_count"] == 1

    response = api_client.delete(f"/api/products/{product_id}/")

    assert response.status_code == 409
    assert response.json()["detail"] == 'Cannot delete product "Widget" because it has 1 relationship.'


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


def test_create_product_with_negative_cost_returns_400(api_client, test_db):
    response = api_client.post(
        "/api/products/",
        {
            "name": "Widget",
            "cost_cents": -1,
            "unit_price_cents": 1234,
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


def test_list_product_categories_returns_seeded_default(api_client, test_db):
    response = api_client.get("/api/product-categories/")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Uncategorized"


def test_create_product_category_returns_201(api_client, test_db):
    response = api_client.post(
        "/api/product-categories/",
        {
            "name": "Labor",
            "description": "Billable work",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Labor"
    assert data["description"] == "Billable work"
    assert data["is_active"] is True


def test_create_duplicate_product_category_returns_clear_400(api_client, test_db):
    first_response = api_client.post(
        "/api/product-categories/",
        {"name": "Labor"},
        format="json",
    )
    assert first_response.status_code == 201

    response = api_client.post(
        "/api/product-categories/",
        {"name": "labor"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == 'A product category named "Labor" already exists.'


def test_get_product_category_detail_returns_metrics_products_and_invoices(
    api_client,
    test_db,
    customer_john_id,
    post_invoice,
):
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Materials", "description": "Physical goods"},
        format="json",
    )
    assert category_response.status_code == 201, category_response.json()
    category_id = category_response.json()["id"]
    product_response = api_client.post(
        "/api/products/",
        {
            "name": "Copper Line Set",
            "cost_cents": 2000,
            "unit_price_cents": 5000,
            "category_id": category_id,
            "is_active": True,
        },
        format="json",
    )
    assert product_response.status_code == 201, product_response.json()
    invoice = post_invoice(customer_id=customer_john_id).json()
    item_response = api_client.post(
        f"/api/invoices/{invoice['id']}/items/",
        {
            "product_id": product_response.json()["id"],
            "quantity": 2,
        },
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()
    status_response = api_client.patch(
        f"/api/invoices/{invoice['id']}/status/",
        {"status": "sent"},
        format="json",
    )
    assert status_response.status_code == 200, status_response.json()

    response = api_client.get(f"/api/product-categories/{category_id}/detail/")

    assert response.status_code == 200
    data = response.json()
    assert data["category"]["name"] == "Materials"
    assert data["metrics"] == {
        "product_count": 1,
        "active_product_count": 1,
        "invoice_count": 1,
        "revenue_total_cents": 10000,
        "cost_total_cents": 4000,
        "profit_total_cents": 6000,
    }
    assert data["products"][0]["name"] == "Copper Line Set"
    assert data["products"][0]["invoice_item_count"] == 1
    assert data["invoices"][0]["id"] == invoice["id"]
    assert data["invoices"][0]["customer_name"] == "John"
    assert data["invoices"][0]["revenue_total_cents"] == 10000
    assert data["invoices"][0]["cost_total_cents"] == 4000
    assert data["invoices"][0]["profit_total_cents"] == 6000


def test_patch_product_category_returns_200(api_client, test_db):
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Labor"},
        format="json",
    )
    category_id = category_response.json()["id"]

    response = api_client.patch(
        f"/api/product-categories/{category_id}/",
        {
            "name": "Updated Labor",
            "description": "Updated",
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Labor"
    assert data["description"] == "Updated"


def test_patch_default_product_category_returns_400(api_client, test_db):
    response = api_client.patch(
        "/api/product-categories/1/",
        {"name": "Default"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The default product category cannot be edited."


def test_patch_duplicate_product_category_returns_clear_400(api_client, test_db):
    labor_response = api_client.post(
        "/api/product-categories/",
        {"name": "Labor"},
        format="json",
    )
    assert labor_response.status_code == 201
    materials_response = api_client.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    category_id = materials_response.json()["id"]

    response = api_client.patch(
        f"/api/product-categories/{category_id}/",
        {"name": "labor"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == 'A product category named "Labor" already exists.'


def test_deactivate_product_category_returns_200(api_client, test_db):
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Labor"},
        format="json",
    )
    category_id = category_response.json()["id"]

    response = api_client.patch(f"/api/product-categories/{category_id}/deactivate/")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_default_product_category_returns_400(api_client, test_db):
    response = api_client.patch("/api/product-categories/1/deactivate/")

    assert response.status_code == 400
    assert response.json()["detail"] == "The default product category cannot be deactivated."


def test_delete_unused_product_category_returns_204(api_client, test_db):
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    category_id = category_response.json()["id"]

    response = api_client.delete(f"/api/product-categories/{category_id}/")

    assert response.status_code == 204


def test_delete_default_product_category_returns_400(api_client, test_db):
    response = api_client.delete("/api/product-categories/1/")

    assert response.status_code == 400
    assert response.json()["detail"] == "The default product category cannot be deleted."


def test_delete_product_category_with_products_returns_409(api_client, test_db):
    category_response = api_client.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    category_id = category_response.json()["id"]
    product_response = api_client.post(
        "/api/products/",
        {
            "name": "Cable",
            "unit_price_cents": 1200,
            "category_id": category_id,
            "is_active": True,
        },
        format="json",
    )
    assert product_response.status_code == 201

    response = api_client.delete(f"/api/product-categories/{category_id}/")

    assert response.status_code == 409
    assert response.json()["detail"] == 'Cannot delete product category "Materials" because 1 product uses it.'
