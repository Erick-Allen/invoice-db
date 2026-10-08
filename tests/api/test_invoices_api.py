from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

INVALID_ID = 9999


def signed_in_client(email, test_db):
    client = APIClient()
    response = client.post(
        "/api/auth/signup/",
        {
            "email": email,
            "password": "StrongPass123!",
            "name": email.split("@")[0],
        },
        format="json",
    )
    assert response.status_code == 201
    return client


def create_customer(api_client, name, email):
    response = api_client.post(
        "/api/customers/",
        {"name": name, "email": email},
        format="json",
    )
    assert response.status_code == 201
    return response.json()


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
    assert response.status_code == 201
    return response.json()

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
    assert data["invoice_number"] == 1
    assert data["customer_id"] == customer_john_id
    assert data["title"] == "Mini split install"
    assert data["description"] == "Installed mini split in upstairs bedroom."
    assert data["date_issued"] == "2026-05-20" 
    assert data["date_due"] == "2026-06-20"
    assert data["subtotal_cents"] == 0
    assert data["tax_rate"] is None
    assert data["tax_cents"] == 0
    assert data["total"] == 0
    assert data["status"] == "draft"
    assert data["location_id"] is None

def test_create_invoice_uses_workspace_default_tax_rate(api_client, test_db, customer_john_id, post_product):
    profile_response = api_client.put(
        "/api/business-profile/",
        {"default_tax_rate": "7.25"},
        format="json",
    )
    assert profile_response.status_code == 200, profile_response.json()

    invoice = create_invoice(api_client, customer_john_id)
    product = post_product(unit_price_cents=10000).json()

    item_response = api_client.post(
        f"/api/invoices/{invoice['id']}/items/",
        {"product_id": product["id"], "quantity": 1},
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()

    response = api_client.get(f"/api/invoices/{invoice['id']}/?include_items=true")
    assert response.status_code == 200
    data = response.json()
    assert data["subtotal_cents"] == 10000
    assert data["tax_rate"] == "7.25"
    assert data["tax_cents"] == 725
    assert data["total"] == 10725

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
    assert data["subtotal_cents"] == 2468
    assert data["tax_cents"] == 0
    assert data["total"] == 2468

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


@pytest.mark.django_db
def test_signed_in_invoices_are_scoped_to_user_workspace(test_db):
    user_a = signed_in_client("invoice-a@example.com", test_db)
    user_b = signed_in_client("invoice-b@example.com", test_db)
    customer_a = create_customer(user_a, "Customer A", "shared@example.com")
    customer_b = create_customer(user_b, "Customer B", "shared@example.com")
    invoice_a = create_invoice(user_a, customer_a["id"])
    invoice_b = create_invoice(user_b, customer_b["id"])

    list_a = user_a.get("/api/invoices/")
    list_b = user_b.get("/api/invoices/")

    assert list_a.status_code == 200
    assert list_b.status_code == 200
    assert [invoice["id"] for invoice in list_a.json()] == [invoice_a["id"]]
    assert [invoice["id"] for invoice in list_b.json()] == [invoice_b["id"]]
    assert [invoice["invoice_number"] for invoice in list_a.json()] == [1]
    assert [invoice["invoice_number"] for invoice in list_b.json()] == [1]


@pytest.mark.django_db
def test_signed_in_invoice_detail_cannot_cross_workspace(test_db):
    user_a = signed_in_client("invoice-detail-a@example.com", test_db)
    user_b = signed_in_client("invoice-detail-b@example.com", test_db)
    customer_a = create_customer(user_a, "Customer A", "customer-a@example.com")
    invoice_a = create_invoice(user_a, customer_a["id"])

    response = user_b.get(f"/api/invoices/{invoice_a['id']}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_signed_in_invoice_is_hidden_from_signed_out_requests(api_client, test_db):
    signed_in = signed_in_client("invoice-owner@example.com", test_db)
    customer = create_customer(signed_in, "Private Customer", "private@example.com")
    invoice = create_invoice(signed_in, customer["id"])

    list_response = api_client.get("/api/invoices/")
    detail_response = api_client.get(f"/api/invoices/{invoice['id']}/")

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404


@pytest.mark.django_db
def test_signed_in_user_cannot_create_invoice_for_other_workspace_customer(test_db):
    user_a = signed_in_client("invoice-customer-a@example.com", test_db)
    user_b = signed_in_client("invoice-customer-b@example.com", test_db)
    customer_a = create_customer(user_a, "Customer A", "customer-a@example.com")

    response = user_b.post(
        "/api/invoices/",
        {
            "customer_id": customer_a["id"],
            "date_issued": "2026-05-20",
            "date_due": "2026-06-20",
        },
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_invoice_child_routes_cannot_cross_workspace(test_db):
    user_a = signed_in_client("invoice-child-a@example.com", test_db)
    user_b = signed_in_client("invoice-child-b@example.com", test_db)
    customer_a = create_customer(user_a, "Customer A", "customer-a@example.com")
    invoice_a = create_invoice(user_a, customer_a["id"])

    item_response = user_b.get(f"/api/invoices/{invoice_a['id']}/items/")
    payment_response = user_b.get(f"/api/invoices/{invoice_a['id']}/payments/")
    payment_summary_response = user_b.get(f"/api/invoices/{invoice_a['id']}/payments/summary/")
    tag_response = user_b.get(f"/api/invoices/{invoice_a['id']}/tags/")

    assert item_response.status_code == 404
    assert payment_response.status_code == 404
    assert payment_summary_response.status_code == 404
    assert tag_response.status_code == 404
