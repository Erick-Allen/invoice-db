# invoice_db/assistant/data_source.py

from typing import Any

from invoice_db.services import customers as customer_services
from invoice_db.services import invoices as invoice_services
from invoice_db.services import exceptions


class ServiceInvoiceAssistantDataSource:
    """Adapter between assistant dispatcher and existing service layer."""

    def __init__(self, cursor, workspace_id: int | None = None):
        self.cursor = cursor
        self.workspace_id = workspace_id

    def count_invoices_by_status(self, status: str) -> int:
        result = invoice_services.count_invoices(
            self.cursor,
            status=status,
            workspace_id=self.workspace_id,
        )

        return result["count"]

    def list_invoices_by_status(self, status: str) -> list[dict[str, Any]]:
        return invoice_services.list_invoices(
            self.cursor,
            status=status,
            workspace_id=self.workspace_id,
        )

    def list_overdue_invoices(self) -> list[dict[str, Any]]:
        return invoice_services.overdue_invoices(
            self.cursor,
            workspace_id=self.workspace_id,
        )

    def list_invoices_by_customer(self, customer_name: str) -> list[dict[str, Any]]:
        customer = self._find_customer_by_name(customer_name)

        return invoice_services.list_invoices(
            self.cursor,
            customer_id=customer["id"],
            workspace_id=self.workspace_id,
        )

    def list_invoices_by_total_range(
        self,
        min_total_cents: int | None = None,
        max_total_cents: int | None = None,
    ) -> list[dict[str, Any]]:
        return invoice_services.list_invoices(
            self.cursor,
            min_total=min_total_cents,
            max_total=max_total_cents,
            workspace_id=self.workspace_id,
        )

    def _find_customer_by_name(self, customer_name: str) -> dict[str, Any]:
        customers = customer_services.list_customers(
            self.cursor,
            workspace_id=self.workspace_id,
        )

        for customer in customers:
            if customer["name"].strip().lower() == customer_name.strip().lower():
                return customer

        raise exceptions.NotFoundError(f"Customer not found (name={customer_name})")
    
    def list_customer_names(self) -> list[str]:
        customers = customer_services.list_customers(
            self.cursor,
            workspace_id=self.workspace_id,
        )
        return [customer["name"] for customer in customers]
