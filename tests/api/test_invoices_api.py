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
            "total": 2000,
        },
        format="json",
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["customer_id"] == customer_john_id
    assert data["date_issued"] == "2026-05-20" 
    assert data["date_due"] == "2026-06-20"
    assert data["total"] == 2000
    assert data["status"] == "draft"

def test_get_invoice_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id, total=1000)
    invoice_id = invoice_response.json()['id']

    response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert response.status_code == 200
    
    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['total'] == 1000

def test_patch_invoice_with_single_field_returns_200(api_client, test_db, customer_john_id, post_invoice,):
    invoice_response = post_invoice(customer_id=customer_john_id, total=1000)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "total": 1500,
        },
        format="json",
    )

    assert response.status_code == 200

    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['total'] == 1500

def test_patch_invoice_with_multiple_fields_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id, total=1000)
    invoice_id = invoice_response.json()['id']

    response = api_client.patch(
        f"/api/invoices/{invoice_id}/",
        {
            "total": 2500,
            "date_due": "2026-07-20"
        },
        format="json",
    )

    assert response.status_code == 200

    data = response.json()
    assert data['id'] == invoice_id
    assert data['customer_id'] == customer_john_id
    assert data['total'] == 2500
    assert data['date_due'] == "2026-07-20"

def test_patch_invoice_status_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id, total=1000)
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

def test_delete_invoice_returns_204(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id, total=1000)
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
            "total": 2000,
        },
        format="json",
    )

    assert response.status_code == 404

def test_create_invoice_with_invalid_total_returns_400(api_client, test_db, customer_john_id):
    response = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
            "total": -1,
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
            "total": 2000,
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
        total=1000,
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
        total=1000,
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