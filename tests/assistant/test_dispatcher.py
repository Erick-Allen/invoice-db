from typing import Any

from invoice_db.assistant.dispatcher import AssistantDispatcher
from invoice_db.assistant.schemas import AssistantIntent, IntentParameters


class FakeInvoiceDataSource:
    def count_invoices_by_status(self, status: str) -> int:
        return 3

    def list_invoices_by_status(self, status: str) -> list[dict[str, Any]]:
        return [
            {"id": 1, "status": status},
            {"id": 2, "status": status},
        ]

    def list_overdue_invoices(self) -> list[dict[str, Any]]:
        return [{"id": 1, "status": "sent"}]

    def list_invoices_by_customer(self, customer_name: str) -> list[dict[str, Any]]:
        return [{"id": 1, "customer_name": customer_name}]

    def list_invoices_by_total_range(
        self,
        min_total_cents: int | None = None,
        max_total_cents: int | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": 1,
                "min_total_cents": min_total_cents,
                "max_total_cents": max_total_cents,
            }
        ]


def test_dispatches_count_invoices_by_status():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="invoices_by_status",
        confidence=0.9,
        parameters=IntentParameters(
            status="paid",
            result_type="count",
        ),
    )

    response = dispatcher.dispatch(intent)

    assert response.intent == "invoices_by_status"
    assert response.message == "There are 3 paid invoices."
    assert response.data == {"status": "paid", "count": 3}


def test_dispatches_list_invoices_by_status():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="invoices_by_status",
        confidence=0.9,
        parameters=IntentParameters(
            status="draft",
            result_type="list",
        ),
    )

    response = dispatcher.dispatch(intent)

    assert response.message == "Found 2 draft invoices."
    assert len(response.data) == 2


def test_dispatches_overdue_invoices():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="list_overdue_invoices",
        confidence=0.9,
        parameters=IntentParameters(),
    )

    response = dispatcher.dispatch(intent)

    assert response.message == "Found 1 overdue invoices."
    assert response.data == [{"id": 1, "status": "sent"}]


def test_dispatches_customer_invoices():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="list_invoices_by_customer",
        confidence=0.9,
        parameters=IntentParameters(customer_name="John Smith"),
    )

    response = dispatcher.dispatch(intent)

    assert response.message == "Found 1 invoices for John Smith."
    assert response.data == [{"id": 1, "customer_name": "John Smith"}]


def test_dispatches_total_range_invoices():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="list_invoices_by_total_range",
        confidence=0.9,
        parameters=IntentParameters(min_total_cents=50000),
    )

    response = dispatcher.dispatch(intent)

    assert response.message == "Found 1 invoices matching that total range."
    assert response.data == [
        {
            "id": 1,
            "min_total_cents": 50000,
            "max_total_cents": None,
        }
    ]


def test_dispatches_unknown_intent():
    dispatcher = AssistantDispatcher(FakeInvoiceDataSource())

    intent = AssistantIntent(
        intent="unknown",
        confidence=0.0,
        parameters=IntentParameters(),
    )

    response = dispatcher.dispatch(intent)

    assert response.intent == "unknown"
    assert response.data is None