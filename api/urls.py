from django.urls import  path

from .views import (
    CustomerListCreateView,
    CustomerDetailView,
    InvoiceListCreateView,
    InvoiceDetailView,
    InvoiceStatusUpdateView,
    ProductListCreateView,
    ProductDetailView,
    ProductDeactivateView,
    AssistantQueryView,
    api_root
)

urlpatterns = [
    path("", api_root, name="api-root"),

    path("customers/", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("customers/<int:customer_id>/", CustomerDetailView.as_view(), name="customer-detail"),

    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/<int:invoice_id>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<int:invoice_id>/status/", InvoiceStatusUpdateView.as_view(), name="invoice-status-update"),

    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<int:product_id>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:product_id>/deactivate/", ProductDeactivateView.as_view(), name="product-deactivate"),

    path ("assistant/query/", AssistantQueryView.as_view(), name="assistant-query"),
]
