INVALID_ID = 9999


def create_invoice(api_client, customer_id):
    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_id,
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


def create_product(api_client, **overrides):
    payload = {
        "name": "Widget",
        "description": "A test widget",
        "cost_cents": 500,
        "unit_price_cents": 1234,
        "is_active": True,
    }
    payload.update(overrides)
    response = api_client.post("/api/products/", payload, format="json")
    assert response.status_code == 201, response.json()
    return response.json()["id"]


def create_invoice_item(api_client, invoice_id, product_id, **overrides):
    payload = {
        "product_id": product_id,
        "quantity": 2,
    }
    payload.update(overrides)
    response = api_client.post(f"/api/invoices/{invoice_id}/items/", payload, format="json")
    assert response.status_code == 201, response.json()
    return response.json()


def test_list_invoice_items_returns_200(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)

    response = api_client.get(f"/api/invoices/{invoice_id}/items/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_invoice_item_returns_201(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_id,
            "quantity": 2,
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["invoice_id"] == invoice_id
    assert data["product_id"] == product_id
    assert data["quantity"] == 2
    assert data["unit_cost_cents"] == 500
    assert data["cost_total_cents"] == 1000
    assert data["unit_price_cents"] == 1234
    assert data["line_total_cents"] == 2468


def test_create_invoice_item_recalculates_invoice_total(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)

    create_invoice_item(api_client, invoice_id, product_id)

    response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert response.status_code == 200
    assert response.json()["total"] == 2468


def test_get_invoice_item_returns_200(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)
    item = create_invoice_item(api_client, invoice_id, product_id)

    response = api_client.get(f"/api/invoice-items/{item['id']}/")

    assert response.status_code == 200
    assert response.json()["id"] == item["id"]


def test_patch_invoice_item_returns_200(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)
    item = create_invoice_item(api_client, invoice_id, product_id)

    response = api_client.patch(
        f"/api/invoice-items/{item['id']}/",
        {
            "quantity": 3,
            "unit_cost_cents": 700,
            "unit_price_cents": 2000,
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 3
    assert data["unit_cost_cents"] == 700
    assert data["cost_total_cents"] == 2100
    assert data["unit_price_cents"] == 2000
    assert data["line_total_cents"] == 6000


def test_patch_invoice_item_product_resets_price(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    first_product_id = create_product(api_client, name="Widget", cost_cents=500, unit_price_cents=1234)
    second_product_id = create_product(api_client, name="Service", cost_cents=1500, unit_price_cents=4000)
    item = create_invoice_item(api_client, invoice_id, first_product_id)

    response = api_client.patch(
        f"/api/invoice-items/{item['id']}/",
        {"product_id": second_product_id},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == second_product_id
    assert data["unit_cost_cents"] == 1500
    assert data["cost_total_cents"] == 3000
    assert data["unit_price_cents"] == 4000
    assert data["line_total_cents"] == 8000


def test_delete_invoice_item_returns_204(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)
    item = create_invoice_item(api_client, invoice_id, product_id)

    response = api_client.delete(f"/api/invoice-items/{item['id']}/")

    assert response.status_code == 204


def test_create_invoice_item_for_locked_invoice_returns_409(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client)
    status_response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {"status": "sent"},
        format="json",
    )
    assert status_response.status_code == 200

    response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {"product_id": product_id},
        format="json",
    )

    assert response.status_code == 409


def test_create_invoice_item_with_inactive_product_returns_400(api_client, test_db, customer_john_id):
    invoice_id = create_invoice(api_client, customer_john_id)
    product_id = create_product(api_client, is_active=False)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {"product_id": product_id},
        format="json",
    )

    assert response.status_code == 400


def test_get_missing_invoice_item_returns_404(api_client, test_db):
    response = api_client.get(f"/api/invoice-items/{INVALID_ID}/")

    assert response.status_code == 404
