INVALID_ID = 9999


def create_tag(api_client, name="Repair", **overrides):
    payload = {
        "name": name,
        "description": "Invoice context",
    }
    payload.update(overrides)

    response = api_client.post("/api/tags/", payload, format="json")
    assert response.status_code == 201
    return response.json()


def create_invoice(api_client, customer_john_id, post_invoice):
    response = post_invoice(customer_john_id)
    assert response.status_code == 201
    return response.json()


def create_tagged_invoice(
    api_client,
    post_invoice,
    post_product,
    customer_id,
    tag_id,
    *,
    cost_cents=1000,
    unit_price_cents=2500,
    quantity=2,
):
    invoice = post_invoice(customer_id=customer_id).json()
    product = post_product(
        name=f"Tagged Product {invoice['id']}",
        cost_cents=cost_cents,
        unit_price_cents=unit_price_cents,
    ).json()
    item_response = api_client.post(
        f"/api/invoices/{invoice['id']}/items/",
        {
            "product_id": product["id"],
            "quantity": quantity,
        },
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()
    tag_response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag_id},
        format="json",
    )
    assert tag_response.status_code == 201, tag_response.json()
    return invoice


def test_list_tags_returns_200(api_client, test_db):
    response = api_client.get("/api/tags/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_tag_returns_201(api_client, test_db):
    response = api_client.post(
        "/api/tags/",
        {
            "name": "Commercial",
            "description": "Commercial work",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Commercial"
    assert data["description"] == "Commercial work"
    assert data["is_active"] is True


def test_create_duplicate_tag_returns_clear_400(api_client, test_db):
    create_tag(api_client, name="Commercial")

    response = api_client.post(
        "/api/tags/",
        {"name": "commercial"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == 'A tag named "Commercial" already exists.'


def test_get_tag_returns_200(api_client, test_db):
    tag = create_tag(api_client)

    response = api_client.get(f"/api/tags/{tag['id']}/")

    assert response.status_code == 200
    assert response.json()["name"] == "Repair"


def test_get_tag_detail_returns_metrics_and_invoices(
    api_client,
    test_db,
    customer_john_id,
    post_invoice,
    post_product,
):
    tag = create_tag(api_client, name="Install")
    sent_invoice = create_tagged_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        tag["id"],
        cost_cents=1000,
        unit_price_cents=2500,
        quantity=2,
    )
    draft_invoice = create_tagged_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        tag["id"],
        cost_cents=500,
        unit_price_cents=3000,
        quantity=1,
    )
    status_response = api_client.patch(
        f"/api/invoices/{sent_invoice['id']}/status/",
        {"status": "sent"},
        format="json",
    )
    assert status_response.status_code == 200, status_response.json()
    payment_response = api_client.post(
        f"/api/invoices/{sent_invoice['id']}/payments/",
        {
            "amount_cents": 1000,
            "payment_date": "2026-01-20",
            "method": "cash",
        },
        format="json",
    )
    assert payment_response.status_code == 201, payment_response.json()

    response = api_client.get(f"/api/tags/{tag['id']}/detail/")

    assert response.status_code == 200
    data = response.json()
    assert data["tag"]["name"] == "Install"
    assert data["metrics"] == {
        "invoice_count": 2,
        "issued_invoice_count": 1,
        "total_invoiced_cents": 5000,
        "total_cost_cents": 2000,
        "total_paid_cents": 1000,
        "net_profit_cents": -1000,
        "total_owed_cents": 4000,
    }
    assert [invoice["id"] for invoice in data["invoices"]] == [draft_invoice["id"], sent_invoice["id"]]
    sent_invoice_data = next(invoice for invoice in data["invoices"] if invoice["id"] == sent_invoice["id"])
    assert sent_invoice_data["customer_name"] == "John"
    assert sent_invoice_data["cost_total_cents"] == 2000
    assert sent_invoice_data["amount_paid_cents"] == 1000
    assert sent_invoice_data["balance_due_cents"] == 4000


def test_patch_tag_returns_200(api_client, test_db):
    tag = create_tag(api_client)

    response = api_client.patch(
        f"/api/tags/{tag['id']}/",
        {
            "name": "Updated Repair",
            "description": "Updated",
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Repair"
    assert data["description"] == "Updated"


def test_patch_duplicate_tag_returns_clear_400(api_client, test_db):
    create_tag(api_client, name="Commercial")
    repair = create_tag(api_client, name="Repair")

    response = api_client.patch(
        f"/api/tags/{repair['id']}/",
        {"name": "commercial"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == 'A tag named "Commercial" already exists.'


def test_deactivate_tag_returns_200(api_client, test_db):
    tag = create_tag(api_client)

    response = api_client.patch(f"/api/tags/{tag['id']}/deactivate/")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_list_tags_active_only_returns_active_tags(api_client, test_db):
    create_tag(api_client, name="Active", is_active=True)
    create_tag(api_client, name="Inactive", is_active=False)

    response = api_client.get("/api/tags/?active_only=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active"


def test_delete_unused_tag_returns_204(api_client, test_db):
    tag = create_tag(api_client)

    response = api_client.delete(f"/api/tags/{tag['id']}/")

    assert response.status_code == 204


def test_delete_missing_tag_returns_404(api_client, test_db):
    response = api_client.delete(f"/api/tags/{INVALID_ID}/")

    assert response.status_code == 404


def test_add_tag_to_invoice_returns_201(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)

    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["invoice_id"] == invoice["id"]
    assert data["tag_id"] == tag["id"]


def test_list_invoice_tags_returns_tags(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)
    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.get(f"/api/invoices/{invoice['id']}/tags/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Repair"


def test_add_duplicate_tag_to_invoice_returns_409(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)
    first_response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )
    assert first_response.status_code == 201

    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == f'Tag "Repair" is already attached to invoice {invoice["id"]}.'


def test_add_inactive_tag_to_invoice_returns_400(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client, is_active=False)

    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive tags cannot be added to invoices."


def test_delete_tag_with_invoice_returns_409(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)
    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.delete(f"/api/tags/{tag['id']}/")

    assert response.status_code == 409
    assert response.json()["detail"] == 'Cannot delete tag "Repair" because 1 invoice uses it.'


def test_remove_tag_from_invoice_returns_204(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)
    response = api_client.post(
        f"/api/invoices/{invoice['id']}/tags/",
        {"tag_id": tag["id"]},
        format="json",
    )
    assert response.status_code == 201

    response = api_client.delete(f"/api/invoices/{invoice['id']}/tags/{tag['id']}/")

    assert response.status_code == 204
    response = api_client.get(f"/api/invoices/{invoice['id']}/tags/")
    assert response.json() == []


def test_remove_missing_tag_from_invoice_returns_404(api_client, test_db, customer_john_id, post_invoice):
    invoice = create_invoice(api_client, customer_john_id, post_invoice)
    tag = create_tag(api_client)

    response = api_client.delete(f"/api/invoices/{invoice['id']}/tags/{tag['id']}/")

    assert response.status_code == 404
