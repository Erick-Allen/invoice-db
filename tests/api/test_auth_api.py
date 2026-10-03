import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_signup_creates_user_and_returns_current_user(api_client):
    response = api_client.post(
        "/api/auth/signup/",
        {
            "email": "new-user@example.com",
            "password": "StrongPass123!",
            "name": "New User",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "new-user@example.com"
    assert response.json()["user"]["name"] == "New User"

    me_response = api_client.get("/api/auth/me/")

    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == "new-user@example.com"


@pytest.mark.django_db
def test_signup_creates_default_workspace(api_client, test_db):
    response = api_client.post(
        "/api/auth/signup/",
        {
            "email": "workspace-user@example.com",
            "password": "StrongPass123!",
            "name": "Workspace User",
        },
        format="json",
    )

    assert response.status_code == 201

    from invoice_db.db import connection

    with connection.db_session(connection.DB_PATH) as (connect, cursor):
        workspace = cursor.execute(
            "SELECT * FROM workspaces WHERE owner_user_id = ?",
            (response.json()["user"]["id"],),
        ).fetchone()

    assert workspace is not None
    assert workspace["name"] == "Workspace User's Workspace"


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(api_client):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPass123!",
    }

    first_response = api_client.post("/api/auth/signup/", payload, format="json")
    second_response = api_client.post("/api/auth/signup/", payload, format="json")

    assert first_response.status_code == 201
    assert second_response.status_code == 400


@pytest.mark.django_db
def test_login_returns_user(api_client, django_user_model):
    django_user_model.objects.create_user(
        username="login@example.com",
        email="login@example.com",
        password="StrongPass123!",
        first_name="Login User",
    )

    response = api_client.post(
        "/api/auth/login/",
        {
            "email": "login@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "login@example.com"
    assert response.json()["user"]["name"] == "Login User"
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(api_client, django_user_model):
    django_user_model.objects.create_user(
        username="login@example.com",
        email="login@example.com",
        password="StrongPass123!",
    )

    response = api_client.post(
        "/api/auth/login/",
        {
            "email": "login@example.com",
            "password": "WrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_me_returns_401_when_signed_out(api_client):
    response = api_client.get("/api/auth/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_clears_current_user(api_client):
    signup_response = api_client.post(
        "/api/auth/signup/",
        {
            "email": "logout@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert signup_response.status_code == 201

    logout_response = api_client.post("/api/auth/logout/")
    me_response = api_client.get("/api/auth/me/")

    assert logout_response.status_code == 204
    assert me_response.status_code == 401


@pytest.mark.django_db
def test_logout_does_not_require_csrf_token(django_user_model, settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    client = APIClient(enforce_csrf_checks=True)
    django_user_model.objects.create_user(
        username="csrf-logout@example.com",
        email="csrf-logout@example.com",
        password="StrongPass123!",
    )

    login_response = client.post(
        "/api/auth/login/",
        {
            "email": "csrf-logout@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )
    logout_response = client.post("/api/auth/logout/")

    assert login_response.status_code == 200
    assert logout_response.status_code == 204
