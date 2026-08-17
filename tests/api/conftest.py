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

@pytest.fixture
def customer_john_id(api_client):
    response = api_client.post(
        "/api/customers/",
        {
            "name": "John",
            "email": "John@test.com",
        },
        format="json",
    )

    return response.json()['id']

@pytest.fixture
def post_invoice(api_client, test_db):
    def helper (
        customer_id, 
        date_issued="2026-05-20",
        date_due="2026-06-20",
    ):
        return api_client.post(
            "/api/invoices/",
            {
                "customer_id": customer_id,
                "date_issued": date_issued,
                "date_due": date_due,
            },
            format="json",
        )
    
    return helper

@pytest.fixture
def post_product(api_client, test_db):
    def helper(
        name="Widget",
        unit_price_cents=1234,
        cost_cents=0,
        description="A test widget",
        is_active=True,
    ):
        return api_client.post(
            "/api/products/",
            {
                "name": name,
                "description": description,
                "cost_cents": cost_cents,
                "unit_price_cents": unit_price_cents,
                "is_active": is_active,
            },
            format="json",
        )

    return helper
