from invoice_db.assistant.service import AssistantService
from invoice_db.assistant.schemas import AssistantResponse, AssistantIntent, IntentParameters


class FakeRouter:
    def route(
        self,
        message: str,
        customer_names: list[str] | None = None,
    ) -> AssistantIntent:
        return AssistantIntent(
            intent="invoices_by_status",
            confidence=0.9,
            parameters=IntentParameters(
                status="paid",
                result_type="count",
            ),
        )


class FakeDispatcher:
    def dispatch(self, assistant_intent: AssistantIntent) -> AssistantResponse:
        return AssistantResponse(
            intent=assistant_intent.intent,
            message="There are 3 paid invoices.",
            data={"status": "paid", "count": 3},
        )


class FakeCustomerNameProvider:
    def list_customer_names(self) -> list[str]:
        return ["John Smith", "Alice Johnson"]


def test_assistant_service_routes_and_dispatches_message():
    service = AssistantService(
        router=FakeRouter(),
        dispatcher=FakeDispatcher(),
        customer_name_provider=FakeCustomerNameProvider(),
    )

    response = service.ask("How many paid invoices do I have?")

    assert response.intent == "invoices_by_status"
    assert response.message == "There are 3 paid invoices."
    assert response.data == {"status": "paid", "count": 3}