from django.urls import  path

from .views import CustomerListCreateView, CustomerDetailView

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("customers/<int:customer_id>/", CustomerDetailView.as_view(), name="customer-detail")
]