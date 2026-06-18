from datetime import date, timedelta


INVALID_ID = 9999


def create_payable_invoice(api_client, customer_john_id, post_invoice, post_product):
    invoice_response = post_invoice(customer_id=customer_john_id)
    assert invoice_response.status_code == 201, invoice_response.json()
    invoice_id = invoice_response.json()["id"]
    product_id = post_product(unit_price_cents=1234).json()["id"]

    item_response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_id,
            "quantity": 1,
        },
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()

    status_response = api_client.patch(
        f"/api/invoices/{invoice_id}/status/",
        {"status": "sent"},
        format="json",
    )
    assert status_response.status_code == 200, status_response.json()

    return invoice_id


def create_payment(api_client, invoice_id, **overrides):
    payload = {
        "amount_cents": 500,
        "payment_date": date.today().isoformat(),
        "method": "cash",
        "note": "Initial payment",
    }
    payload.update(overrides)
    response = api_client.post(f"/api/invoices/{invoice_id}/payments/", payload, format="json")
    assert response.status_code == 201, response.json()
    return response.json()


def test_list_payments_returns_200(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()["id"]

    response = api_client.get(f"/api/invoices/{invoice_id}/payments/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_payment_returns_201(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 500,
            "payment_date": date.today().isoformat(),
            "method": "cash",
            "note": "Initial payment",
        },
        format="json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["invoice_id"] == invoice_id
    assert data["amount_cents"] == 500
    assert data["method"] == "cash"
    assert data["note"] == "Initial payment"


def test_create_full_payment_marks_invoice_paid(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 1234,
            "payment_date": date.today().isoformat(),
            "method": "card",
        },
        format="json",
    )
    assert response.status_code == 201, response.json()

    invoice_response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert invoice_response.status_code == 200
    assert invoice_response.json()["status"] == "paid"


def test_get_payment_returns_200(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    payment = create_payment(api_client, invoice_id)

    response = api_client.get(f"/api/payments/{payment['id']}/")

    assert response.status_code == 200
    assert response.json()["id"] == payment["id"]


def test_list_payments_returns_created_payments(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    payment = create_payment(api_client, invoice_id)

    response = api_client.get(f"/api/invoices/{invoice_id}/payments/")

    assert response.status_code == 200
    assert response.json()[0]["id"] == payment["id"]


def test_payment_summary_returns_200(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    create_payment(api_client, invoice_id)

    response = api_client.get(f"/api/invoices/{invoice_id}/payments/summary/")

    assert response.status_code == 200
    data = response.json()
    assert data["invoice_id"] == invoice_id
    assert data["invoice_total_cents"] == 1234
    assert data["amount_paid_cents"] == 500
    assert data["balance_due_cents"] == 734
    assert data["is_paid"] is False


def test_delete_payment_returns_204(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    payment = create_payment(api_client, invoice_id)

    response = api_client.delete(f"/api/payments/{payment['id']}/")

    assert response.status_code == 204
    list_response = api_client.get(f"/api/invoices/{invoice_id}/payments/")
    assert list_response.json() == []


def test_delete_payment_reopens_paid_invoice(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    payment = create_payment(api_client, invoice_id, amount_cents=1234)

    response = api_client.delete(f"/api/payments/{payment['id']}/")

    assert response.status_code == 204
    invoice_response = api_client.get(f"/api/invoices/{invoice_id}/")
    assert invoice_response.json()["status"] == "sent"


def test_create_payment_for_draft_invoice_returns_409(api_client, test_db, customer_john_id, post_invoice):
    invoice_response = post_invoice(customer_id=customer_john_id)
    invoice_id = invoice_response.json()["id"]

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 500,
            "payment_date": date.today().isoformat(),
            "method": "cash",
        },
        format="json",
    )

    assert response.status_code == 409


def test_create_payment_over_balance_returns_400(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 1235,
            "payment_date": date.today().isoformat(),
            "method": "cash",
        },
        format="json",
    )

    assert response.status_code == 400


def test_create_payment_future_date_returns_400(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)
    future_date = (date.today() + timedelta(days=1)).isoformat()

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 500,
            "payment_date": future_date,
            "method": "cash",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "future" in response.json()["detail"]


def test_create_payment_invalid_method_returns_400(api_client, test_db, customer_john_id, post_invoice, post_product):
    invoice_id = create_payable_invoice(api_client, customer_john_id, post_invoice, post_product)

    response = api_client.post(
        f"/api/invoices/{invoice_id}/payments/",
        {
            "amount_cents": 500,
            "payment_date": date.today().isoformat(),
            "method": "crypto",
        },
        format="json",
    )

    assert response.status_code == 400


def test_get_missing_payment_returns_404(api_client, test_db):
    response = api_client.get(f"/api/payments/{INVALID_ID}/")

    assert response.status_code == 404


def test_payment_summary_missing_invoice_returns_404(api_client, test_db):
    response = api_client.get(f"/api/invoices/{INVALID_ID}/payments/summary/")

    assert response.status_code == 404
