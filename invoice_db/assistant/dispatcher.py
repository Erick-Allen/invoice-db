from typing import Any, Protocol

from invoice_db.assistant.schemas import AssistantIntent, AssistantResponse

class InvoiceAssistantDataSource(Protocol):
    """Methods the assistant dispatcher needs from the app layer."""

    def count_invoices_by_status(self, status: str) -> int:
        ...

    def list_invoices_by_status(self, status: str) -> list[dict[str, Any]]:
        ...

    def list_overdue_invoices(self) -> list[dict[str, Any]]:
        ...

    def list_invoices_by_customer(self, customer_name: str) -> list[dict[str, Any]]:
        ...

    def list_invoices_by_total_range(
            self, 
            min_total_cents: int | None = None,
            max_total_cents: int | None = None,
    ) -> list[dict[str, Any]]:
        ...

class AssistantDispatcher:
    def __init__(self, data_source: InvoiceAssistantDataSource):
        self.data_source = data_source

    def dispatch(self, assistant_intent: AssistantIntent) -> AssistantResponse:
        intent = assistant_intent.intent
        params = assistant_intent.parameters

        if intent == "unknown":
            return AssistantResponse(
                intent="unknown",
                message="I couldn't match that request to a supported invoice action.",
                data=None,
            )

        if intent == "invoices_by_status":
            if params.status is None or params.result_type is None:
                return self._invalid_parameters(intent)

            if params.result_type == "count":
                count = self.data_source.count_invoices_by_status(params.status)

                return AssistantResponse(
                    intent=intent,
                    message=f"There are {count} {params.status} invoices.",
                    data={
                        "status": params.status,
                        "count": count,
                    },
                )

            invoices = self.data_source.list_invoices_by_status(params.status)

            return AssistantResponse(
                intent=intent,
                message=f"Found {len(invoices)} {params.status} invoices.",
                data=invoices,
            )

        if intent == "list_overdue_invoices":
            invoices = self.data_source.list_overdue_invoices()

            return AssistantResponse(
                intent=intent,
                message=f"Found {len(invoices)} overdue invoices.",
                data=invoices,
            )

        if intent == "list_invoices_by_customer":
            if params.customer_name is None:
                return self._invalid_parameters(intent)

            invoices = self.data_source.list_invoices_by_customer(params.customer_name)

            return AssistantResponse(
                intent=intent,
                message=f"Found {len(invoices)} invoices for {params.customer_name}.",
                data=invoices,
            )

        if intent == "list_invoices_by_total_range":
            invoices = self.data_source.list_invoices_by_total_range(
                min_total_cents=params.min_total_cents,
                max_total_cents=params.max_total_cents,
            )

            return AssistantResponse(
                intent=intent,
                message=f"Found {len(invoices)} invoices matching that total range.",
                data=invoices,
            )

        return AssistantResponse(
            intent="unknown",
            message="I couldn't match that request to a supported invoice action.",
            data=None,
        )

    def _invalid_parameters(self, intent: str) -> AssistantResponse:
        return AssistantResponse(
            intent="unknown",
            message=f"The request matched '{intent}', but required details were missing.",
            data=None,
        )