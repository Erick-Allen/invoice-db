def create_tag(api_client, name):
    response = api_client.post(
        "/api/tags/",
        {"name": name, "description": None},
        format="json",
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_report_invoice(
    api_client,
    post_invoice,
    post_product,
    customer_id,
    *,
    date_issued,
    cost_cents,
    unit_price_cents,
    quantity,
    tag_id=None,
):
    invoice_response = post_invoice(
        customer_id=customer_id,
        date_issued=date_issued,
        date_due="2026-12-31",
    )
    assert invoice_response.status_code == 201, invoice_response.json()
    invoice_id = invoice_response.json()["id"]

    product_response = post_product(
        name=f"Product {invoice_id}",
        cost_cents=cost_cents,
        unit_price_cents=unit_price_cents,
    )
    assert product_response.status_code == 201, product_response.json()

    item_response = api_client.post(
        f"/api/invoices/{invoice_id}/items/",
        {
            "product_id": product_response.json()["id"],
            "quantity": quantity,
        },
        format="json",
    )
    assert item_response.status_code == 201, item_response.json()

    if tag_id is not None:
        tag_response = api_client.post(
            f"/api/invoices/{invoice_id}/tags/",
            {"tag_id": tag_id},
            format="json",
        )
        assert tag_response.status_code == 201, tag_response.json()

    return invoice_id


def test_reporting_overview_returns_performance_and_breakdowns(
    api_client,
    test_db,
    customer_john_id,
    post_invoice,
    post_product,
):
    commercial = create_tag(api_client, "Commercial")
    repair = create_tag(api_client, "Repair")

    sent_invoice_id = create_report_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        date_issued="2026-01-15",
        cost_cents=1000,
        unit_price_cents=2500,
        quantity=2,
        tag_id=commercial["id"],
    )
    draft_invoice_id = create_report_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        date_issued="2026-02-15",
        cost_cents=1000,
        unit_price_cents=3000,
        quantity=1,
        tag_id=repair["id"],
    )
    void_invoice_id = create_report_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        date_issued="2026-03-15",
        cost_cents=500,
        unit_price_cents=2000,
        quantity=1,
    )

    sent_response = api_client.patch(
        f"/api/invoices/{sent_invoice_id}/status/",
        {"status": "sent"},
        format="json",
    )
    assert sent_response.status_code == 200, sent_response.json()

    payment_response = api_client.post(
        f"/api/invoices/{sent_invoice_id}/payments/",
        {
            "amount_cents": 1000,
            "payment_date": "2026-01-20",
            "method": "cash",
        },
        format="json",
    )
    assert payment_response.status_code == 201, payment_response.json()

    void_sent_response = api_client.patch(
        f"/api/invoices/{void_invoice_id}/status/",
        {"status": "sent"},
        format="json",
    )
    assert void_sent_response.status_code == 200, void_sent_response.json()
    void_response = api_client.patch(
        f"/api/invoices/{void_invoice_id}/status/",
        {"status": "void"},
        format="json",
    )
    assert void_response.status_code == 200, void_response.json()

    response = api_client.get("/api/reports/overview/")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == {
        "invoice_count": 1,
        "revenue_total_cents": 5000,
        "cost_total_cents": 2000,
        "profit_total_cents": 3000,
        "outstanding_due_cents": 4000,
    }
    assert data["status_breakdown"] == [
        {"status": "draft", "invoice_count": 1, "revenue_total_cents": 3000},
        {"status": "sent", "invoice_count": 1, "revenue_total_cents": 5000},
        {"status": "void", "invoice_count": 1, "revenue_total_cents": 2000},
    ]
    assert data["tag_performance"] == [
        {
            "tag_id": commercial["id"],
            "tag_name": "Commercial",
            "invoice_count": 1,
            "revenue_total_cents": 5000,
            "cost_total_cents": 2000,
            "profit_total_cents": 3000,
        },
    ]


def test_reporting_overview_filters_by_date_range(
    api_client,
    test_db,
    customer_john_id,
    post_invoice,
    post_product,
):
    create_report_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        date_issued="2026-01-15",
        cost_cents=1000,
        unit_price_cents=2500,
        quantity=1,
    )
    march_invoice_id = create_report_invoice(
        api_client,
        post_invoice,
        post_product,
        customer_john_id,
        date_issued="2026-03-15",
        cost_cents=500,
        unit_price_cents=2000,
        quantity=1,
    )
    sent_response = api_client.patch(
        f"/api/invoices/{march_invoice_id}/status/",
        {"status": "sent"},
        format="json",
    )
    assert sent_response.status_code == 200, sent_response.json()

    response = api_client.get(
        "/api/reports/overview/?start_date=2026-03-01&end_date=2026-03-31"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2026-03-01"
    assert data["end_date"] == "2026-03-31"
    assert data["summary"]["invoice_count"] == 1
    assert data["summary"]["revenue_total_cents"] == 2000
    assert data["summary"]["cost_total_cents"] == 500


def test_reporting_overview_rejects_invalid_date_range(api_client, test_db):
    response = api_client.get(
        "/api/reports/overview/?start_date=2026-04-01&end_date=2026-03-01"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "End date cannot be before start date."
