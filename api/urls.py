from django.urls import  path

from .views import (
    CustomerListCreateView,
    CustomerDetailView,
    InvoiceListCreateView,
    InvoiceDetailView,
    InvoiceStatusUpdateView,
)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("customers/<int:customer_id>/", CustomerDetailView.as_view(), name="customer-detail"),

    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/<int:invoice_id>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<int:invoice_id>/status/", InvoiceStatusUpdateView.as_view(), name="invoice-status-update")
]