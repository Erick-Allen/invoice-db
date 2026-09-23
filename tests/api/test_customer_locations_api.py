def _create_location(api_client, customer_id, **overrides):
    payload = {
        "label": "Home",
        "address_line1": "123 Main St",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32801",
    }
    payload.update(overrides)
    return api_client.post(
        f"/api/customers/{customer_id}/locations/",
        payload,
        format="json",
    )


def _create_supplier(api_client, name="Johnstone", **overrides):
    payload = {
        "name": name,
        "phone": "555-0100",
        "email": "source@example.com",
        "website": "https://example.com",
    }
    payload.update(overrides)
    response = api_client.post("/api/suppliers/", payload, format="json")
    assert response.status_code == 201, response.json()
    return response.json()


def _create_supplier_location(api_client, supplier_id, **overrides):
    payload = {
        "label": "Counter",
        "address_line1": "789 Supplier Way",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32803",
    }
    payload.update(overrides)
    return api_client.post(
        f"/api/suppliers/{supplier_id}/locations/",
        payload,
        format="json",
    )


def test_create_customer_location(api_client, test_db, customer_john_id):
    response = _create_location(api_client, customer_john_id)

    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == customer_john_id
    assert data["label"] == "Home"
    assert data["is_primary"] is True


def test_list_customer_locations(api_client, test_db, customer_john_id):
    _create_location(api_client, customer_john_id)

    response = api_client.get(f"/api/customers/{customer_john_id}/locations/")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Home"


def test_update_customer_location(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()

    response = api_client.patch(
        f"/api/customers/{customer_john_id}/locations/{location['id']}/",
        {"label": "Main Office", "notes": "Call first"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["label"] == "Main Office"
    assert response.json()["notes"] == "Call first"


def test_delete_customer_location(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()

    response = api_client.delete(f"/api/customers/{customer_john_id}/locations/{location['id']}/")

    assert response.status_code == 204


def test_delete_customer_location_keeps_global_location(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()

    before_delete = api_client.get("/api/locations/")
    response = api_client.delete(f"/api/customers/{customer_john_id}/locations/{location['id']}/")
    after_delete = api_client.get("/api/locations/")

    assert before_delete.status_code == 200
    assert before_delete.json()[0]["id"] == location["location_id"]
    assert before_delete.json()[0]["assigned_customer_count"] == 1
    assert response.status_code == 204
    assert after_delete.status_code == 200
    assert after_delete.json()[0]["id"] == location["location_id"]
    assert after_delete.json()[0]["assigned_customer_count"] == 0


def test_list_locations_generalizes_customer_and_supplier_assignments(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()
    supplier = _create_supplier(api_client)
    _create_supplier_location(
        api_client,
        supplier["id"],
        address_line1=location["address_line1"],
        city=location["city"],
        state=location["state"],
        postal_code=location["postal_code"],
        country=location["country"],
    )

    response = api_client.get("/api/locations/")

    assert response.status_code == 200
    data = response.json()[0]
    assert data["id"] == location["location_id"]
    assert data["assigned_customer_count"] == 1
    assert data["assigned_supplier_count"] == 1
    assert data["assigned_count"] == 2
    assert data["assigned_customer_names"] == "John"
    assert data["assigned_supplier_names"] == "Johnstone"
    assert data["assigned_names"] == "John, Johnstone"


def test_create_standalone_location(api_client, test_db):
    response = api_client.post(
        "/api/locations/",
        {
            "address_line1": "789 Standalone Ave",
            "city": "Orlando",
            "state": "FL",
            "postal_code": "32804",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["address_line1"] == "789 Standalone Ave"
    assert data["assigned_customer_count"] == 0


def test_create_duplicate_standalone_location_returns_400(api_client, test_db):
    payload = {
        "address_line1": "789 Standalone Ave",
        "city": "Orlando",
        "state": "FL",
        "postal_code": "32804",
    }
    first_response = api_client.post("/api/locations/", payload, format="json")
    assert first_response.status_code == 201

    response = api_client.post("/api/locations/", {**payload, "address_line1": " 789 standalone ave "}, format="json")

    assert response.status_code == 400
    assert response.json()["detail"] == "That location already exists."


def test_get_location_detail(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()
    invoice = api_client.post(
        "/api/invoices/",
        {
            "customer_id": customer_john_id,
            "location_id": location["id"],
            "date_issued": "2026-09-01",
            "date_due": "2026-09-30",
        },
        format="json",
    ).json()

    response = api_client.get(f"/api/locations/{location['location_id']}/")

    assert response.status_code == 200
    data = response.json()
    assert data["location"]["id"] == location["location_id"]
    assert data["customer_assignments"][0]["id"] == location["id"]
    assert data["customer_assignments"][0]["customer_id"] == customer_john_id
    assert data["supplier_assignments"] == []
    assert data["invoices"][0]["id"] == invoice["id"]
    assert data["invoices"][0]["customer_location_id"] == location["id"]


def test_update_location_detail_address(api_client, test_db, customer_john_id):
    location = _create_location(api_client, customer_john_id).json()

    response = api_client.patch(
        f"/api/locations/{location['location_id']}/",
        {
            "address_line1": "456 New Rd",
            "address_line2": "",
            "city": "Winter Park",
            "state": "FL",
            "postal_code": "32789",
        },
        format="json",
    )
    assignment_response = api_client.get(f"/api/customers/{customer_john_id}/locations/{location['id']}/")

    assert response.status_code == 200
    data = response.json()
    assert data["address_line1"] == "456 New Rd"
    assert data["address_line2"] is None
    assert data["city"] == "Winter Park"
    assert assignment_response.json()["address_line1"] == "456 New Rd"


def test_location_must_belong_to_customer(api_client, test_db, customer_john_id):
    other_customer = api_client.post(
        "/api/customers/",
        {"name": "Alice", "email": "alice@test.com"},
        format="json",
    ).json()
    location = _create_location(api_client, customer_john_id).json()

    response = api_client.get(f"/api/customers/{other_customer['id']}/locations/{location['id']}/")

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]


def test_create_supplier_location(api_client, test_db):
    supplier = _create_supplier(api_client)

    response = _create_supplier_location(api_client, supplier["id"])

    assert response.status_code == 201
    data = response.json()
    assert data["supplier_id"] == supplier["id"]
    assert data["label"] == "Counter"
    assert data["is_primary"] is True


def test_list_supplier_locations(api_client, test_db):
    supplier = _create_supplier(api_client)
    _create_supplier_location(api_client, supplier["id"])

    response = api_client.get(f"/api/suppliers/{supplier['id']}/locations/")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Counter"


def test_delete_supplier_location_keeps_global_location(api_client, test_db):
    supplier = _create_supplier(api_client)
    location = _create_supplier_location(api_client, supplier["id"]).json()

    before_delete = api_client.get("/api/locations/")
    response = api_client.delete(f"/api/suppliers/{supplier['id']}/locations/{location['id']}/")
    after_delete = api_client.get("/api/locations/")

    assert before_delete.status_code == 200
    assert before_delete.json()[0]["id"] == location["location_id"]
    assert response.status_code == 204
    assert after_delete.status_code == 200
    assert after_delete.json()[0]["id"] == location["location_id"]


def test_get_location_detail_includes_supplier_assignments(api_client, test_db):
    supplier = _create_supplier(api_client)
    location = _create_supplier_location(api_client, supplier["id"]).json()

    response = api_client.get(f"/api/locations/{location['location_id']}/")

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_assignments"][0]["id"] == location["id"]
    assert data["supplier_assignments"][0]["supplier_id"] == supplier["id"]
    assert data["supplier_assignments"][0]["supplier_name"] == "Johnstone"


def test_supplier_location_must_belong_to_supplier(api_client, test_db):
    supplier = _create_supplier(api_client)
    other_supplier = _create_supplier(api_client, name="Carrier", email="carrier@example.com")
    location = _create_supplier_location(api_client, supplier["id"]).json()

    response = api_client.get(f"/api/suppliers/{other_supplier['id']}/locations/{location['id']}/")

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]
