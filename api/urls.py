from django.urls import  path

from .views import (
    CustomerListCreateView,
    CustomerDetailView,
    InvoiceListCreateView,
    InvoiceDetailView,
    InvoiceStatusUpdateView,
    InvoiceItemListCreateView,
    InvoiceItemDetailView,
    PaymentListCreateView,
    PaymentSummaryView,
    PaymentDetailView,
    ProductCategoryListCreateView,
    ProductCategoryDetailView,
    ProductCategoryDeactivateView,
    ProductListCreateView,
    ProductDetailView,
    ProductSupplierListCreateView,
    ProductSupplierDetailView,
    ProductDeactivateView,
    SupplierListCreateView,
    SupplierDetailView,
    SupplierDeactivateView,
    SupplierProductsView,
    SupplierRemoveFromProductsView,
    TagListCreateView,
    TagDetailView,
    TagDeactivateView,
    InvoiceTagListCreateView,
    InvoiceTagDetailView,
    ReportingOverviewView,
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
    path("invoices/<int:invoice_id>/items/", InvoiceItemListCreateView.as_view(), name="invoice-item-list-create"),
    path("invoices/<int:invoice_id>/tags/", InvoiceTagListCreateView.as_view(), name="invoice-tag-list-create"),
    path("invoices/<int:invoice_id>/tags/<int:tag_id>/", InvoiceTagDetailView.as_view(), name="invoice-tag-detail"),
    path("invoices/<int:invoice_id>/payments/", PaymentListCreateView.as_view(), name="payment-list-create"),
    path("invoices/<int:invoice_id>/payments/summary/", PaymentSummaryView.as_view(), name="payment-summary"),
    path("invoice-items/<int:invoice_item_id>/", InvoiceItemDetailView.as_view(), name="invoice-item-detail"),
    
    path("payments/<int:payment_id>/", PaymentDetailView.as_view(), name="payment-detail"),

    path("reports/overview/", ReportingOverviewView.as_view(), name="reporting-overview"),

    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<int:product_id>/suppliers/", ProductSupplierListCreateView.as_view(), name="product-supplier-list-create"),
    path("products/<int:product_id>/suppliers/<int:supplier_id>/", ProductSupplierDetailView.as_view(), name="product-supplier-detail"),
    path("product-categories/", ProductCategoryListCreateView.as_view(), name="product-category-list-create"),
    path("product-categories/<int:category_id>/", ProductCategoryDetailView.as_view(), name="product-category-detail"),
    path("product-categories/<int:category_id>/deactivate/", ProductCategoryDeactivateView.as_view(), name="product-category-deactivate"),
    path("products/<int:product_id>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:product_id>/deactivate/", ProductDeactivateView.as_view(), name="product-deactivate"),

    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("suppliers/<int:supplier_id>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path("suppliers/<int:supplier_id>/deactivate/", SupplierDeactivateView.as_view(), name="supplier-deactivate"),
    path("suppliers/<int:supplier_id>/products/", SupplierProductsView.as_view(), name="supplier-products"),
    path("suppliers/<int:supplier_id>/remove-from-products/", SupplierRemoveFromProductsView.as_view(), name="supplier-remove-from-products"),

    path("tags/", TagListCreateView.as_view(), name="tag-list-create"),
    path("tags/<int:tag_id>/", TagDetailView.as_view(), name="tag-detail"),
    path("tags/<int:tag_id>/deactivate/", TagDeactivateView.as_view(), name="tag-deactivate"),

    path ("assistant/query/", AssistantQueryView.as_view(), name="assistant-query"),
]
