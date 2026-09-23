from datetime import date, timedelta

INVALID_ID = 9999

def test_list_invoices_returns_200(api_client, test_db):
    response = api_client.get("/api/invoices/")

    assert response.status_code == 200
    assert response.json() == []

def test_list_invoices_filters_by_customer_id(api_client, test_db, customer_john_id, post_invoice):
    john_invoice = post_invoice(customer_id=customer_john_id).json()
    other_customer = api_client.post(
        "/api/customers/",
        {"name": "Alice", "email": "alice@test.com"},
        format="json",
    ).json()
    post_invoice(customer_id=other_customer["id"])

    response = api_client.get(f"/api/invoices/?customer_id={customer_john_id}&include_items=true")

    assert response.status_code == 200
    data = response.json()
    assert [invoice["id"] for invoice in data] == [john_invoice["id"]]
    assert data[0]["customer_id"] == customer_john_id
    assert data[0]["items"] == []
    assert data[0]["cost_total_cents"] == 0
    assert data[0]["profit_total_cents"] == 0

def test_create_invoice_returns_201(api_client, test_db, customer_john_id):
    response =  api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "title": "Mini split install",
            "description": "Installed mini split in upstairs bedroom.",
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
        },
        format="json",
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["customer_id"] == customer_john_id
    assert data["title"] == "Mini split install"
    assert data["description"] == "Installed mini split in upstairs bedroom."
    assert data["date_issued"] == "2026-05-20" 
    assert data["date_due"] == "2026-06-20"
    assert data["total"] == 0
    assert data["status"] == "draft"
    assert data["location_id"] is None

def test_create_invoice_with_location(api_client, test_db, customer_john_id):
    location_response = api_client.post(
        f"/api/customers/{customer_john_id}/locations/",
        {
            "label": "Home",
            "address_line1": "123 Main St",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
        },
        format="json",
    )
    location_id = location_response.json()["id"]

    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "location_id": location_id,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["location_id"] == location_id

def test_create_invoice_rejects_other_customer_location(api_client, test_db, customer_john_id):
    other_customer = api_client.post(
        "/api/customers/",
        {"name": "Alice", "email": "alice@test.com"},
        format="json",
    ).json()
    location = api_client.post(
        f"/api/customers/{other_customer['id']}/locations/",
        {
            "label": "Office",
            "address_line1": "456 Office Rd",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
        },
        format="json",
    ).json()

    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "location_id": location["id"],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]

def test_get_invoice_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert response.status_code == 200
    
    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['total'] == 0

def test_get_invoice_include_items_returns_line_items(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']
    product_id = post_product(cost_cents=500, unit_price_cents=1234).json()["id"]

    item_response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_id,
            "quantity": 2,
        },
        format="json",
    )
    assert item_response.status_code == 201

    response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert response.status_code == 200
    assert "items" not in response.json()

    response = api_client.get(f"/api/invoices/{invoice_id}/?include_items=true")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == invoice_id
    assert data["items"] == [
        {
            "id": item_response.json()["id"],
            "invoice_id": invoice_id,
            "product_id": product_id,
            "quantity": 2,
            "unit_cost_cents": 500,
            "cost_total_cents": 1000,
            "unit_price_cents": 1234,
            "line_total_cents": 2468,
            "profit_total_cents": 1468,
        }
    ]
    assert data["cost_total_cents"] == 1000
    assert data["profit_total_cents"] == 1468
    assert data["profit_margin_percent"] == 59.48

def test_list_invoices_include_items_returns_line_items(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']
    product_id = post_product(unit_price_cents=1234).json()["id"]

    item_response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_id,
            "quantity": 2,
        },
        format="json",
    )
    assert item_response.status_code == 201

    response = api_client.get("/api/invoices/")
    assert response.status_code == 200
    assert "items" not in response.json()[0]

    response = api_client.get("/api/invoices/?include_items=true")
    assert response.status_code == 200

    data = response.json()
    assert data[0]["id"] == invoice_id
    assert data[0]["items"][0]["id"] == item_response.json()["id"]
    assert data[0]["items"][0]["line_total_cents"] == 2468
    assert data[0]["items"][0]["profit_total_cents"] == 2468
    assert data[0]["cost_total_cents"] == 0
    assert data[0]["profit_total_cents"] == 2468
    assert data[0]["profit_margin_percent"] == 100.0

def test_patch_invoice_with_single_field_returns_200(api_client, test_db, customer_john_id, post_invoice,):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "date_due": "2026-07-20",
        },
        format="json",
    )

    assert response.status_code == 200

    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['date_due'] == "2026-07-20"


def test_patch_invoice_title_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "title": "Maintenance visit",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Maintenance visit"


def test_patch_invoice_title_can_clear(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']
    api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "title": "Maintenance visit",
        },
        format="json",
    )

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "title": None,
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["title"] is None


def test_patch_invoice_description_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "description": "Replaced capacitor and verified system pressures.",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Replaced capacitor and verified system pressures."


def test_patch_invoice_description_can_clear(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']
    api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "description": "Replaced capacitor and verified system pressures.",
        },
        format="json",
    )

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "description": None,
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["description"] is None

def test_patch_invoice_location(api_client, test_db, customer_john_id, post_invoice):
    invoice_id = post_invoice(customer_id=customer_john_id).json()["id"]
    location = api_client.post(
        f"/api/customers/{customer_john_id}/locations/",
        {
            "label": "Home",
            "address_line1": "123 Main St",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
        },
        format="json",
    ).json()

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {"location_id": location["id"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["location_id"] == location["id"]

def test_patch_invoice_can_clear_location(api_client, test_db, customer_john_id, post_invoice):
    location = api_client.post(
        f"/api/customers/{customer_john_id}/locations/",
        {
            "label": "Home",
            "address_line1": "123 Main St",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
        },
        format="json",
    ).json()
    invoice_id = post_invoice(customer_id=customer_john_id).json()["id"]
    api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {"location_id": location["id"]},
        format="json",
    )

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {"location_id": None},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["location_id"] is None

def test_patch_invoice_with_multiple_fields_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "date_issued": "2026-05-21",
            "date_due": "2026-07-20"
        },
        format="json",
    )

    assert response.status_code == 200

    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['date_issued'] == "2026-05-21"
    assert data['date_due'] == "2026-07-20"

def test_patch_invoice_status_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id, date_issued=None, date_due=None)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {
            "status": "sent"
        },
        fomrat="json",
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == invoice_id
    assert data["status"] == "sent"
    assert data["date_issued"] == date.today().isoformat()
    assert data["date_due"] == (date.today() + timedelta(days=30)).isoformat()

def test_patch_invoice_status_rejects_manual_sent_to_paid(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    sent_response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {
            "status": "sent"
        },
        format="json",
    )
    assert sent_response.status_code == 200

    paid_response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {
            "status": "paid"
        },
        format="json",
    )

    assert paid_response.status_code == 400
    assert "Invalid transition sent -> paid" in paid_response.json()["detail"]

def test_patch_invoice_status_rejects_inactive_line_item_product(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']
    product_response = post_product(name="Inactive Widget")
    product_id = product_response.json()["id"]

    item_response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_id,
            "quantity": 1,
        },
        format="json",
    )
    assert item_response.status_code == 201

    deactivate_response = api_client.patch(f"/api/products/{product_id}/deactivate/")
    assert deactivate_response.status_code == 200

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {
            "status": "sent"
        },
        format="json",
    )

    assert response.status_code == 400
    assert "inactive products" in response.json()["detail"]
    assert "Inactive Widget" in response.json()["detail"]

def test_delete_invoice_returns_204(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()['id']

    response = api_client.delete(f"/api/invoices/{invoice_id}/")

    assert response.status_code == 204

# Negative Tests
def test_create_invoice_with_missing_customer_returns_404(api_client, test_db):
    response =  api_client.post(
        "/api/invoices/",
        {
            "customer_id": INVALID_ID,
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
        },
        format="json",
    )

    assert response.status_code == 404

def test_create_invoice_with_manual_total_returns_400(api_client, test_db, customer_john_id):
    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
            "total": 1000,
        },
        fomrat="json",
    )

    assert response.status_code == 400

def test_create_invoice_with_due_date_before_issued_date_returns_400(api_client, test_db, customer_john_id, post_invoice):
    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "date_issued": "2026-06-20",
            "date_due": "2026-05-20",
        },
        fomrat="json",
    )

    assert response.status_code == 400

def test_get_missing_invoice_returns_404(api_client, test_db, customer_john_id, post_invoice):
    response = api_client.get(F"/api/invoices/{INVALID_ID}/")

    assert response.status_code == 404

def test_patch_invoice_with_empty_body_returns_400(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(
        customer_id=customer_john_id,
    )
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {},
        format="json",
    )

    assert response.status_code == 400

def test_patch_invoice_status_with_invalid_status_returns_400(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(
        customer_id=customer_john_id,
    )
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {
            "status": "invalid_status"
        },
        format="json",
    )

    assert response.status_code == 400

def test_delete_missing_invoice_returns_404(api_client, test_db, customer_john_id, post_invoice):
    response = api_client.delete("/api/invoices/9999/")

    assert response.status_code == 404
