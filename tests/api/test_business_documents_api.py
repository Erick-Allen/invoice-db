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
    assert response.status_code == 201, response.json()


def _document_content(text: str = "Check condenser coils before replacing parts.") -> dict:
    return {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Diagnostic Steps"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            },
        ],
    }


@pytest.mark.django_db
def test_signed_out_user_cannot_access_documents(signed_out_api_client, test_db):
    response = signed_out_api_client.get("/api/documents/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_create_and_list_business_documents(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "documents@example.com")

    create_response = signed_out_api_client.post(
        "/api/documents/",
        {
            "title": "Commercial Refrigeration Diagnostics",
            "category": "Service",
            "content_json": _document_content(),
        },
        format="json",
    )
    list_response = signed_out_api_client.get("/api/documents/")

    assert create_response.status_code == 201, create_response.json()
    created = create_response.json()
    assert created["title"] == "Commercial Refrigeration Diagnostics"
    assert created["category"] == "Service"
    assert created["content_text"] == (
        "Diagnostic Steps\n"
        "Check condenser coils before replacing parts."
    )
    assert list_response.status_code == 200
    assert list_response.json() == [created]


@pytest.mark.django_db
def test_documents_default_blank_category_to_general(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "documents-category@example.com")

    response = signed_out_api_client.post(
        "/api/documents/",
        {
            "title": "Overdue Customer Policy",
            "category": "",
            "content_json": _document_content("Call after seven days overdue."),
        },
        format="json",
    )

    assert response.status_code == 201, response.json()
    assert response.json()["category"] == "General"


@pytest.mark.django_db
def test_get_update_and_delete_business_document(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "documents-crud@example.com")
    create_response = signed_out_api_client.post(
        "/api/documents/",
        {
            "title": "Old Title",
            "content_json": _document_content("Old body."),
        },
        format="json",
    )
    document_id = create_response.json()["id"]

    detail_response = signed_out_api_client.get(f"/api/documents/{document_id}/")
    update_response = signed_out_api_client.patch(
        f"/api/documents/{document_id}/",
        {
            "title": "Warranty Policy",
            "category": "Policy",
            "content_json": _document_content("Labor warranty lasts thirty days."),
        },
        format="json",
    )
    delete_response = signed_out_api_client.delete(f"/api/documents/{document_id}/")
    missing_response = signed_out_api_client.get(f"/api/documents/{document_id}/")

    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Old Title"
    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["title"] == "Warranty Policy"
    assert update_response.json()["category"] == "Policy"
    assert update_response.json()["content_text"] == (
        "Diagnostic Steps\n"
        "Labor warranty lasts thirty days."
    )
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


@pytest.mark.django_db
def test_documents_are_workspace_scoped(test_db):
    user_a = APIClient()
    user_b = APIClient()
    _signup(user_a, "documents-a@example.com")
    _signup(user_b, "documents-b@example.com")

    create_response = user_a.post(
        "/api/documents/",
        {
            "title": "User A Document",
            "content_json": _document_content("Only user A can see this."),
        },
        format="json",
    )
    document_id = create_response.json()["id"]

    assert create_response.status_code == 201, create_response.json()
    assert user_a.get("/api/documents/").json()[0]["title"] == "User A Document"
    assert user_b.get("/api/documents/").json() == []
    assert user_b.get(f"/api/documents/{document_id}/").status_code == 404
    assert user_b.patch(
        f"/api/documents/{document_id}/",
        {"title": "Hijacked"},
        format="json",
    ).status_code == 404
    assert user_b.delete(f"/api/documents/{document_id}/").status_code == 404


@pytest.mark.django_db
def test_guest_user_can_create_temporary_document(signed_out_api_client, test_db):
    guest_response = signed_out_api_client.post("/api/auth/guest/")

    assert guest_response.status_code == 201

    document_response = signed_out_api_client.post(
        "/api/documents/",
        {
            "title": "Guest Note",
            "content_json": _document_content("Temporary note."),
        },
        format="json",
    )

    assert document_response.status_code == 201, document_response.json()
    assert document_response.json()["title"] == "Guest Note"


@pytest.mark.django_db
def test_document_rejects_invalid_editor_content(signed_out_api_client, test_db):
    _signup(signed_out_api_client, "documents-invalid@example.com")

    response = signed_out_api_client.post(
        "/api/documents/",
        {
            "title": "Invalid",
            "content_json": {"type": "paragraph"},
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Document content must be a TipTap document."
