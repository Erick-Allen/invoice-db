INVALID_ID = 9999

def test_list_invoices_returns_200(api_client, test_db):
    response = api_client.get("/api/invoices/")

    assert response.status_code == 200
    assert response.json() == []

def test_create_invoice_returns_201(api_client, test_db, customer_john_id):
    response =  api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
        },
        format="json",
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["customer_id"] == customer_john_id
    assert data["date_issued"] == "2026-05-20" 
    assert data["date_due"] == "2026-06-20"
    assert data["total"] == 0
    assert data["status"] == "draft"

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
            "unit_cost_cents": 0,
            "cost_total_cents": 0,
            "unit_price_cents": 1234,
            "line_total_cents": 2468,
        }
    ]

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
    invoice_response = post_invoice(customer_id=customer_john_id)
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
