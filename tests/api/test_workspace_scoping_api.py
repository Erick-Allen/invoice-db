import pytest
from rest_framework.test import APIClient

from invoice_db.assistant.schemas import AssistantIntent, IntentParameters
from invoice_db.assistant.data_source import ServiceInvoiceAssistantDataSource
from invoice_db.db import connection
from invoice_db.services import workspaces as workspace_services


pytestmark = pytest.mark.django_db


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
    assert response.status_code == 201, response.json()
    return client, response.json()["user"]["id"]


def create_customer(api_client, name="Customer", email="customer@example.com"):
    response = api_client.post(
        "/api/customers/",
        {"name": name, "email": email},
        format="json",
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_invoice(api_client, customer_id):
    response = api_client.post(
        "/api/invoices/",
        {"customer_id": customer_id},
        format="json",
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_product(api_client, name="Copper Pipe", unit_price_cents=1500, cost_cents=700):
    response = api_client.post(
        "/api/products/",
        {
            "name": name,
            "unit_price_cents": unit_price_cents,
            "cost_cents": cost_cents,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    return response.json()


def test_catalog_data_is_scoped_and_same_names_are_allowed(test_db):
    user_a, _ = signed_in_client("catalog-a@example.com", test_db)
    user_b, _ = signed_in_client("catalog-b@example.com", test_db)

    category_a = user_a.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    category_b = user_b.post(
        "/api/product-categories/",
        {"name": "Materials"},
        format="json",
    )
    product_a = create_product(user_a)
    product_b = create_product(user_b)
    supplier_a = user_a.post("/api/suppliers/", {"name": "Carrier"}, format="json")
    supplier_b = user_b.post("/api/suppliers/", {"name": "Carrier"}, format="json")
    tag_a = user_a.post("/api/tags/", {"name": "Repair"}, format="json")
    tag_b = user_b.post("/api/tags/", {"name": "Repair"}, format="json")

    assert category_a.status_code == 201, category_a.json()
    assert category_b.status_code == 201, category_b.json()
    assert supplier_a.status_code == 201, supplier_a.json()
    assert supplier_b.status_code == 201, supplier_b.json()
    assert tag_a.status_code == 201, tag_a.json()
    assert tag_b.status_code == 201, tag_b.json()

    assert user_a.get("/api/products/").json() == [product_a]
    assert user_b.get("/api/products/").json() == [product_b]
    assert user_b.get(f"/api/products/{product_a['id']}/").status_code == 404
    assert user_b.get(f"/api/suppliers/{supplier_a.json()['id']}/").status_code == 404
    assert user_b.get(f"/api/tags/{tag_a.json()['id']}/").status_code == 404
    assert user_b.get(f"/api/product-categories/{category_a.json()['id']}/detail/").status_code == 404


def test_cross_workspace_catalog_relationships_are_rejected(test_db):
    user_a, _ = signed_in_client("relationship-a@example.com", test_db)
    user_b, _ = signed_in_client("relationship-b@example.com", test_db)
    product_a = create_product(user_a)
    supplier_b = user_b.post("/api/suppliers/", {"name": "Cross Supplier"}, format="json").json()
    customer_a = create_customer(user_a, "Scoped Customer", "scoped@example.com")
    invoice_a = create_invoice(user_a, customer_a["id"])
    tag_b = user_b.post("/api/tags/", {"name": "Other Tag"}, format="json").json()

    supplier_response = user_a.post(
        f"/api/products/{product_a['id']}/suppliers/",
        {"supplier_id": supplier_b["id"]},
        format="json",
    )
    tag_response = user_a.post(
        f"/api/invoices/{invoice_a['id']}/tags/",
        {"tag_id": tag_b["id"]},
        format="json",
    )

    assert supplier_response.status_code == 404
    assert tag_response.status_code == 404


def test_reports_and_assistant_data_source_are_workspace_scoped(test_db):
    user_a, user_a_id = signed_in_client("report-a@example.com", test_db)
    user_b, user_b_id = signed_in_client("report-b@example.com", test_db)
    customer_a = create_customer(user_a, "Report Customer", "report@example.com")
    invoice_a = create_invoice(user_a, customer_a["id"])
    product_a = create_product(user_a, unit_price_cents=5000, cost_cents=2000)

    item_response = user_a.post(
        f"/api/invoices/{invoice_a['id']}/items/",
        {"product_id": product_a["id"], "quantity": 1},
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()
    sent_response = user_a.patch(
        f"/api/invoices/{invoice_a['id']}/status/",
        {"status": "sent"},
        format="json",
    )
    assert sent_response.status_code == 200, sent_response.json()

    report_a = user_a.get("/api/reports/overview/").json()
    report_b = user_b.get("/api/reports/overview/").json()

    assert report_a["summary"]["invoice_count"] == 1
    assert report_a["summary"]["revenue_total_cents"] == 5000
    assert report_b["summary"]["invoice_count"] == 0
    assert report_b["summary"]["revenue_total_cents"] == 0

    with connection.db_session(connection.DB_PATH) as (connect, cursor):
        workspace_a = workspace_services.get_or_create_default_workspace(
            cursor,
            owner_user_id=user_a_id,
            owner_label="report-a",
        )
        workspace_b = workspace_services.get_or_create_default_workspace(
            cursor,
            owner_user_id=user_b_id,
            owner_label="report-b",
        )
        source_a = ServiceInvoiceAssistantDataSource(cursor, workspace_id=workspace_a["id"])
        source_b = ServiceInvoiceAssistantDataSource(cursor, workspace_id=workspace_b["id"])

        assert source_a.count_invoices_by_status("sent") == 1
        assert source_b.count_invoices_by_status("sent") == 0


def test_assistant_query_uses_signed_in_workspace_not_unowned_data(api_client, test_db, monkeypatch):
    legacy_customer = create_customer(api_client, "Legacy Customer", "legacy@example.com")
    create_invoice(api_client, legacy_customer["id"])
    signed_in, _ = signed_in_client("assistant-scope@example.com", test_db)

    def route_to_draft_count(message, customer_names=None):
        assert customer_names == []
        return AssistantIntent(
            intent="invoices_by_status",
            confidence=1.0,
            parameters=IntentParameters(status="draft", result_type="count"),
        )

    monkeypatch.setattr("api.views.router.route", route_to_draft_count)

    response = signed_in.post(
        "/api/assistant/query/",
        {"message": "How many draft invoices?"},
        format="json",
    )

    assert response.status_code == 200, response.json()
    assert response.json()["assistant_response"]["data"]["count"] == 0


def test_locations_do_not_cross_workspace_boundaries(api_client, test_db):
    user_a, _ = signed_in_client("location-a@example.com", test_db)
    user_b, _ = signed_in_client("location-b@example.com", test_db)
    customer_a = create_customer(user_a, "Location Customer", "location@example.com")
    location_response = user_a.post(
        f"/api/customers/{customer_a['id']}/locations/",
        {
            "label": "Shop",
            "address_line1": "123 Scoped St",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32801",
        },
        format="json",
    )
    assert location_response.status_code == 201, location_response.json()
    global_location_id = location_response.json()["location_id"]

    assert user_a.get("/api/locations/").json()[0]["id"] == global_location_id
    assert user_b.get("/api/locations/").json() == []
    assert api_client.get("/api/locations/").json() == []
    assert user_b.get(f"/api/locations/{global_location_id}/").status_code == 404
    assert api_client.get(f"/api/locations/{global_location_id}/").status_code == 404


def test_signed_in_workspaces_can_create_the_same_location_address(test_db):
    user_a, _ = signed_in_client("same-location-a@example.com", test_db)
    user_b, _ = signed_in_client("same-location-b@example.com", test_db)
    customer_a = create_customer(user_a, "Location A", "location-a@example.com")
    customer_b = create_customer(user_b, "Location B", "location-b@example.com")
    payload = {
        "label": "Shop",
        "address_line1": "456 Shared Ave",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32801",
    }

    location_a = user_a.post(
        f"/api/customers/{customer_a['id']}/locations/",
        payload,
        format="json",
    )
    location_b = user_b.post(
        f"/api/customers/{customer_b['id']}/locations/",
        payload,
        format="json",
    )

    assert location_a.status_code == 201, location_a.json()
    assert location_b.status_code == 201, location_b.json()
    assert location_a.json()["location_id"] != location_b.json()["location_id"]
    assert [location["id"] for location in user_a.get("/api/locations/").json()] == [
        location_a.json()["location_id"]
    ]
    assert [location["id"] for location in user_b.get("/api/locations/").json()] == [
        location_b.json()["location_id"]
    ]


def test_signed_in_workspaces_can_create_the_same_standalone_location(test_db):
    user_a, _ = signed_in_client("standalone-location-a@example.com", test_db)
    user_b, _ = signed_in_client("standalone-location-b@example.com", test_db)
    payload = {
        "address_line1": "789 Shared Standalone Ave",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32804",
    }

    location_a = user_a.post("/api/locations/", payload, format="json")
    location_b = user_b.post("/api/locations/", payload, format="json")

    assert location_a.status_code == 201, location_a.json()
    assert location_b.status_code == 201, location_b.json()
    assert location_a.json()["id"] != location_b.json()["id"]
    assert user_a.get("/api/locations/").json()[0]["id"] == location_a.json()["id"]
    assert user_b.get("/api/locations/").json()[0]["id"] == location_b.json()["id"]
