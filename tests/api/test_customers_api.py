import pytest
from rest_framework.test import APIClient

from invoice_db.db import connection
from invoice_db.db import schema

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"

    monkeypatch.setattr(connection, "DB_PATH", str(db_path))

    with connection.db_session(connection.DB_PATH) as (connect, cursor):
        schema.create_schema(cursor)

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='customers'"
        )
        assert cursor.fetchone() is not None


    return db_path

def create_customer(api_client, name, email):
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
    create_response = create_customer(api_client, name="John", email="john@example.com")

    customer_id = create_response.json()['id']
    response = api_client.get(f"/api/customers/{customer_id}/")
    assert response.status_code == 200
    data = response.json()

    assert data['id'] == customer_id
    assert data['name'] == "John"
    assert data['email'] == "john@example.com"

def test_patch_customer_returns_200(api_client, test_db):
    create_response = create_customer(api_client, name="Old Name", email="old@example.com")

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
    create_response = create_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.delete(f"/api/customers/{customer_id}/")
    assert response.status_code == 204

# Negative Tests
def test_create_customer_with_blank_name_returns_400(api_client, test_db):
    response = create_customer(api_client, name=" ", email="john@example.com")
    assert response.status_code == 400

def test_create_customer_with_invalid_email_returns_400(api_client, test_db):
    response = create_customer(api_client, name="John", email="not-an-email")
    assert response.status_code == 400

def test_create_customer_with_duplicate_email_returns_400(api_client, test_db):
    create_response = create_customer(api_client, name="John", email="john@example.com")
    response = create_customer(api_client, name="John Duplicate", email="john@example.com")
    assert create_response.status_code == 201
    assert response.status_code == 400

def test_get_missing_customer_returns_404(api_client, test_db):
    response = api_client.get("/api/customers/9999/")
    assert response.status_code == 404

def test_patch_customer_with_empty_body_returns_400(api_client, test_db):
    create_response = create_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {},
        format="json"
    )
    assert response.status_code == 400


def test_patch_customer_with_duplicate_email_returns_400(api_client, test_db):
    create_response = create_customer(api_client, name="John", email="john@example.com")
    customer_id = create_response.json()['id']
    response = api_client.patch(
        f"/api/customers/{customer_id}/",
        {"email": "john@example.com"},
        fomrat="json"
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