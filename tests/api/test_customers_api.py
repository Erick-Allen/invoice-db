import pytest
from rest_framework.test import APIClient


def post_customer(api_client, name, email):
        return api_client.post(
            "/api/customers/",
            {
                "name": name,
                "email": email,
            },
            format="json",
        )

def test_list_customers_returns_200(api_client, test_db):
    response = api_client.get("/api/customers/")

    assert response.status_code == 200
    assert response.json() == []

def test_create_customer_returns_201(api_client, test_db):
    response = api_client.post(
        "/api/customers/",
        {
            "name": "John",
            "email": "john@example.com",
        },
        format="json"
    )

    assert response.status_code == 201
    data = response.json()

    assert data['id'] == 1
    assert data['name'] == "John"
    assert data['email'] == "john@example.com"

def test_get_customer_returns_200(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")

    customer_id = create_response.json()['id']
    response = api_client.get(f"/api/customers/{customer_id}/")
    assert response.status_code == 200
    data = response.json()

    assert data['id'] == customer_id
    assert data['name'] == "John"
    assert data['email'] == "john@example.com"

def test_patch_customer_with_single_fields_returns_200(api_client, test_db):
    pass

def test_patch_customer_with_multiple_fields_returns_200(api_client, test_db):
    create_response = post_customer(api_client, name="Old Name", email="old@example.com")

    customer_id = create_response.json()['id']

    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {"name": "New Name"},
        format="json",
    )

    assert response.status_code == 200
    data = response.json()

    assert data['id'] == customer_id
    assert data['name'] == "New Name"
    assert data['email'] == "old@example.com"

def test_delete_customer_returns_204(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.delete(f"/api/customers/{customer_id}/")
    assert response.status_code == 204

# Negative Tests
def test_create_customer_with_blank_name_returns_400(api_client, test_db):
    response = post_customer(api_client, name=" ", email="john@example.com")
    assert response.status_code == 400

def test_create_customer_with_invalid_email_returns_400(api_client, test_db):
    response = post_customer(api_client, name="John", email="not-an-email")
    assert response.status_code == 400

def test_create_customer_with_invalid_phone_returns_400(api_client, test_db):
    response = api_client.post(
        "/api/customers/",
        {
            "name": "John",
            "email": "john@example.com",
            "phone": "555CALLNOW",
        },
        format="json",
    )
    assert response.status_code == 400

def test_create_customer_with_short_phone_returns_400(api_client, test_db):
    response = api_client.post(
        "/api/customers/",
        {
            "name": "John",
            "email": "john@example.com",
            "phone": "5550100",
        },
        format="json",
    )
    assert response.status_code == 400

def test_create_customer_with_duplicate_email_returns_400(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")
    response = post_customer(api_client, name="John Duplicate", email="john@example.com")
    assert create_response.status_code == 201
    assert response.status_code == 400

def test_get_missing_customer_returns_404(api_client, test_db):
    response = api_client.get("/api/customers/9999/")
    assert response.status_code == 404

def test_patch_customer_with_empty_body_returns_400(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {},
        format="json"
    )
    assert response.status_code == 400


def test_patch_customer_with_duplicate_email_returns_400(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {"email": "john@example.com"},
        fomrat="json"
    )
    assert response.status_code == 400

def test_patch_customer_with_invalid_phone_returns_400(api_client, test_db):
    create_response = post_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {"phone": "555CALLNOW"},
        format="json",
    )
    assert response.status_code == 400

def test_patch_missing_customer_returns_404(api_client, test_db):
    response = api_client.patch(
        "/api/customers/9999/",
        {"name": "Missing"},
        format="json"
    )
    assert response.status_code == 404

def test_delete_missing_customer_returns_404(api_client, test_db):
    response = api_client.delete("/api/customers/9999/")
    assert response.status_code == 404


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


@pytest.mark.django_db
def test_signed_in_customers_are_scoped_to_user_workspace(test_db):
    user_a = signed_in_client("owner-a@example.com", test_db)
    user_b = signed_in_client("owner-b@example.com", test_db)

    created_a = post_customer(user_a, name="Shared Email A", email="shared@example.com")
    created_b = post_customer(user_b, name="Shared Email B", email="shared@example.com")

    assert created_a.status_code == 201
    assert created_b.status_code == 201

    list_a = user_a.get("/api/customers/")
    list_b = user_b.get("/api/customers/")

    assert list_a.status_code == 200
    assert list_b.status_code == 200
    assert [customer["name"] for customer in list_a.json()] == ["Shared Email A"]
    assert [customer["name"] for customer in list_b.json()] == ["Shared Email B"]


@pytest.mark.django_db
def test_signed_in_customer_detail_cannot_cross_workspace(test_db):
    user_a = signed_in_client("detail-a@example.com", test_db)
    user_b = signed_in_client("detail-b@example.com", test_db)

    created_a = post_customer(user_a, name="Private Customer", email="private@example.com")
    customer_id = created_a.json()["id"]

    response = user_b.get(f"/api/customers/{customer_id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_signed_in_customer_is_hidden_from_signed_out_requests(api_client, test_db):
    signed_in = signed_in_client("private-owner@example.com", test_db)
    created = post_customer(signed_in, name="Private Customer", email="private@example.com")
    customer_id = created.json()["id"]

    list_response = api_client.get("/api/customers/")
    detail_response = api_client.get(f"/api/customers/{customer_id}/")

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert detail_response.status_code == 404
