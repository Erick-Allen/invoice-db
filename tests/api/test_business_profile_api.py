import pytest
from rest_framework.test import APIClient


def _signup(client: APIClient, email: str) -> None:
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


@pytest.mark.django_db
def test_signed_out_user_cannot_access_business_profile(signed_out_api_client, test_db):
    response = signed_out_api_client.get("/api/business-profile/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_get_business_profile_returns_empty_profile_for_workspace(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "profile-empty@example.com")

    response = signed_out_api_client.get("/api/business-profile/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] is None
    assert data["workspace_id"] is not None
    assert data["business_name"] is None
    assert data["default_payment_terms_days"] is None
    assert data["ways_to_pay"] is None
    assert data["default_tax_rate"] is None
    assert data["default_invoice_footer"] is None


@pytest.mark.django_db
def test_put_business_profile_creates_and_updates_workspace_profile(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "profile-save@example.com")

    create_response = signed_out_api_client.put(
        "/api/business-profile/",
        {
            "business_name": "  Allen Studio  ",
            "email": "billing@example.com",
            "phone": "555-555-5555",
            "website": "https://example.com",
            "address_line1": "123 Main St",
            "address_line2": "",
            "city": "Atlanta",
            "state": "GA",
            "postal_code": "30301",
            "default_payment_terms_days": 15,
            "ways_to_pay": "Zelle: billing@example.com",
            "default_tax_rate": "7.255",
            "default_invoice_footer": "Thanks for working with us.",
        },
        format="json",
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["business_name"] == "Allen Studio"
    assert created["address_line2"] is None
    assert created["default_payment_terms_days"] == 15
    assert created["ways_to_pay"] == "Zelle: billing@example.com"
    assert created["default_tax_rate"] == "7.255"

    update_response = signed_out_api_client.put(
        "/api/business-profile/",
        {
            "business_name": "Allen Studio LLC",
            "default_payment_terms_days": 0,
        },
        format="json",
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["business_name"] == "Allen Studio LLC"
    assert updated["default_payment_terms_days"] == 0
    assert updated["email"] is None


@pytest.mark.django_db
def test_business_profile_rejects_non_numeric_payment_terms(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "profile-payment-terms@example.com")

    response = signed_out_api_client.put(
        "/api/business-profile/",
        {"default_payment_terms_days": "Due on receipt"},
        format="json",
    )

    assert response.status_code == 400
    assert "default_payment_terms_days" in response.json()


@pytest.mark.django_db
def test_business_profile_rejects_tax_rates_over_seven_digits(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "profile-tax-rate@example.com")

    response = signed_out_api_client.put(
        "/api/business-profile/",
        {"default_tax_rate": "12345678"},
        format="json",
    )

    assert response.status_code == 400
    assert "default_tax_rate" in response.json()


@pytest.mark.django_db
def test_business_profile_tax_rate_updates_existing_untaxed_drafts(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "profile-tax-drafts@example.com")
    customer_response = signed_out_api_client.post(
        "/api/customers/",
        {"name": "Tax Customer", "email": "tax-draft@example.com"},
        format="json",
    )
    product_response = signed_out_api_client.post(
        "/api/products/",
        {"name": "Compressor", "unit_price_cents": 10000, "cost_cents": 5000},
        format="json",
    )
    invoice_response = signed_out_api_client.post(
        "/api/invoices/",
        {"customer_id": customer_response.json()["id"]},
        format="json",
    )
    item_response = signed_out_api_client.post(
        f"/api/invoices/{invoice_response.json()['id']}/items/",
        {"product_id": product_response.json()["id"], "quantity": 1},
        format="json",
    )

    assert customer_response.status_code == 201
    assert product_response.status_code == 201
    assert invoice_response.status_code == 201
    assert item_response.status_code == 201

    profile_response = signed_out_api_client.put(
        "/api/business-profile/",
        {"default_tax_rate": "7.25"},
        format="json",
    )
    invoice_detail_response = signed_out_api_client.get(
        f"/api/invoices/{invoice_response.json()['id']}/?include_items=true"
    )

    assert profile_response.status_code == 200
    assert invoice_detail_response.status_code == 200
    invoice = invoice_detail_response.json()
    assert invoice["subtotal_cents"] == 10000
    assert invoice["tax_rate"] == "7.25"
    assert invoice["tax_cents"] == 725
    assert invoice["total"] == 10725


@pytest.mark.django_db
def test_business_profiles_are_workspace_scoped(test_db):
    user_a = APIClient()
    user_b = APIClient()
    _signup(user_a, "profile-a@example.com")
    _signup(user_b, "profile-b@example.com")

    response_a = user_a.put(
        "/api/business-profile/",
        {"business_name": "User A Business"},
        format="json",
    )
    response_b = user_b.get("/api/business-profile/")

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_b.json()["business_name"] is None
    assert response_b.json()["workspace_id"] != response_a.json()["workspace_id"]


@pytest.mark.django_db
def test_guest_user_can_save_temporary_business_profile(signed_out_api_client, test_db):
    guest_response = signed_out_api_client.post("/api/auth/guest/")

    assert guest_response.status_code == 201

    profile_response = signed_out_api_client.put(
        "/api/business-profile/",
        {"business_name": "Guest Business"},
        format="json",
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["business_name"] == "Guest Business"
