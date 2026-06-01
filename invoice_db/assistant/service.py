# invoice_db/assistant/service.py

from typing import Protocol

from invoice_db.assistant.dispatcher import AssistantDispatcher
from invoice_db.assistant.router import AssistantRouter
from invoice_db.assistant.schemas import AssistantResponse


class CustomerNameProvider(Protocol):
    def list_customer_names(self) -> list[str]:
        ...


class AssistantService:
    """End-to-end assistant service."""

    def __init__(
        self,
        router: AssistantRouter,
        dispatcher: AssistantDispatcher,
        customer_name_provider: CustomerNameProvider | None = None,
    ):
        self.router = router
        self.dispatcher = dispatcher
        self.customer_name_provider = customer_name_provider

    def ask(self, message: str) -> AssistantResponse:
        customer_names = []

        if self.customer_name_provider is not None:
            customer_names = self.customer_name_provider.list_customer_names()

        assistant_intent = self.router.route(
            message=message,
            customer_names=customer_names,
        )

        return self.dispatcher.dispatch(assistant_intent)