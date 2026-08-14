import sqlite3

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from invoice_db.db import connection
from invoice_db.services import customers as customer_services
from invoice_db.services import invoices as invoice_services
from invoice_db.services import invoice_items as invoice_item_services
from invoice_db.services import payments as payment_services
from invoice_db.services import product_categories as product_category_services
from invoice_db.services import products as product_services
from invoice_db.services.exceptions import  ValidationError, NotFoundError, ServiceError, ConflictError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from invoice_db.assistant.router import AssistantRouter
from invoice_db.assistant.dispatcher import AssistantDispatcher
from invoice_db.assistant.data_source import ServiceInvoiceAssistantDataSource
from invoice_db.services.customers import list_customers
from scripts.seed import get_connection

from .serializers import (
    CustomerSerializer,
    CustomerUpdateSerializer,
    InvoiceCreateSerializer,
    InvoiceSerializer,
    InvoiceUpdateSerializer,
    InvoiceStatusUpdateSerializer,
    InvoiceItemSerializer,
    InvoiceItemCreateSerializer,
    InvoiceItemUpdateSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentSummarySerializer,
    ProductCategorySerializer,
    ProductCategoryUpdateSerializer,
    ProductSerializer,
    ProductUpdateSerializer,
)

router = AssistantRouter(use_qwen=True)

def _include_items(request) -> bool:
    return request.query_params.get("include_items", "").lower() in {"1", "true", "yes"}

def _with_invoice_items(cursor, invoice: dict) -> dict:
    invoice_data = dict(InvoiceSerializer(invoice).data)
    invoice_items = invoice_item_services.list_invoice_items(cursor, invoice_id=invoice_data["id"])
    invoice_data["items"] = InvoiceItemSerializer(invoice_items, many=True).data
    return invoice_data

@api_view(["GET"])
def api_root(request):
    return Response(
        {
            "message": "Invoice DB API",
            "endpoints": {
                "customers": "/api/customers/",
                "invoices": "/api/invoices",
                "products": "/api/products/",
            }
        }
    )

class CustomerListCreateView(APIView):
    def get(self, request):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                customer = customer_services.list_customers(cursor)

        except sqlite3.Error:
            return Response(
                {"detail": "Something went wrong while retieving customers."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        serializer = CustomerSerializer(customer, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CustomerSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                customer = customer_services.create_customer(
                cursor,
                customer_name=serializer.validated_data['name'],
                customer_email=serializer.validated_data['email'],
                )
        
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while creating the customer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class CustomerDetailView(APIView):
    def get(self, request, customer_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                customer = customer_services.get_customer_by_id(cursor, customer_id=customer_id)
        
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while creating the customer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,

            )
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, customer_id):
        serializer = CustomerUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                customer = customer_services.update_customer_by_id(
                    cursor,
                    customer_id=customer_id,
                    new_name=serializer.validated_data.get("name"),
                    new_email=serializer.validated_data.get("email")
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while creating the customer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, customer_id):
        try:
             with connection.db_session(connection.DB_PATH) as (connect, cursor):
                 customer_services.delete_customer_by_id(cursor, customer_id=customer_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while creating the customer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the customer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class InvoiceListCreateView(APIView):
    def get(self, request):
        include_items = _include_items(request)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoices = invoice_services.list_invoices(cursor=cursor)
                if include_items:
                    invoices = [_with_invoice_items(cursor, invoice) for invoice in invoices]

        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving invoices."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if include_items:
            return Response(invoices, status=status.HTTP_200_OK)
        
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = InvoiceCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        date_issued = serializer.validated_data.get("date_issued")
        date_due = serializer.validated_data.get("date_due")

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice = invoice_services.create_invoice(
                    cursor,
                    customer_id=serializer.validated_data['customer_id'],
                    date_issued=date_issued.isoformat() if date_issued else None,
                    date_due=date_due.isoformat() if date_due else None,
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while creating the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class InvoiceDetailView(APIView):
    def get(self, request, invoice_id):
        include_items = _include_items(request)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice = invoice_services.get_invoice_by_id(
                    cursor=cursor,
                    invoice_id=invoice_id
                )
                if include_items:
                    invoice = _with_invoice_items(cursor, invoice)

        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if include_items:
            return Response(invoice, status=status.HTTP_200_OK)
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, invoice_id):
        serializer = InvoiceUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        date_issued = serializer.validated_data.get("date_issued")
        date_due = serializer.validated_data.get("date_due")

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice = invoice_services.update_invoice_by_id(
                    cursor,
                    invoice_id=invoice_id,
                    new_date_issued=date_issued.isoformat() if date_issued else None,
                    new_date_due=date_due.isoformat() if date_due else None,
                    new_customer_id=serializer.validated_data.get("customer_id"),
                )
        
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while updating the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while updating the invoice"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, invoice_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_services.delete_invoice(cursor, invoice_id=invoice_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while deleting the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deleting the invoice"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class InvoiceStatusUpdateView(APIView):
    def patch(self, request, invoice_id):
        serializer = InvoiceStatusUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice = invoice_services.set_invoice_status(
                    cursor,
                    invoice_id=invoice_id,
                    new_status=serializer.validated_data['status'],
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError as e:
            return Response(
                {"detail": "Something went wrong while updating the invoice status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while updating the invoice status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            )
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InvoiceItemListCreateView(APIView):
    def get(self, request, invoice_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_items = invoice_item_services.list_invoice_items(cursor, invoice_id=invoice_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving invoice items."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = InvoiceItemSerializer(invoice_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, invoice_id):
        serializer = InvoiceItemCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_item = invoice_item_services.create_invoice_item(
                    cursor,
                    invoice_id=invoice_id,
                    product_id=serializer.validated_data["product_id"],
                    quantity=serializer.validated_data.get("quantity", 1),
                    unit_price_cents=serializer.validated_data.get("unit_price_cents"),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while creating the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = InvoiceItemSerializer(invoice_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class InvoiceItemDetailView(APIView):
    def get(self, request, invoice_item_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_item = invoice_item_services.get_invoice_item_by_id(
                    cursor,
                    invoice_item_id=invoice_item_id,
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = InvoiceItemSerializer(invoice_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, invoice_item_id):
        serializer = InvoiceItemUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_item = invoice_item_services.update_invoice_item_by_id(
                    cursor,
                    invoice_item_id=invoice_item_id,
                    product_id=serializer.validated_data.get("product_id"),
                    quantity=serializer.validated_data.get("quantity"),
                    unit_price_cents=serializer.validated_data.get("unit_price_cents"),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while updating the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while updating the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = InvoiceItemSerializer(invoice_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, invoice_item_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice_item_services.delete_invoice_item(cursor, invoice_item_id=invoice_item_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deleting the invoice item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class PaymentListCreateView(APIView):
    def get(self, request, invoice_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                payments = payment_services.list_payments(cursor, invoice_id=invoice_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving payments."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, invoice_id):
        serializer = PaymentCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_date = serializer.validated_data["payment_date"]

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                payment = payment_services.create_payment(
                    cursor,
                    invoice_id=invoice_id,
                    amount_cents=serializer.validated_data["amount_cents"],
                    payment_date=payment_date.isoformat(),
                    method=serializer.validated_data["method"],
                    note=serializer.validated_data.get("note"),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while creating the payment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the payment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PaymentSummaryView(APIView):
    def get(self, request, invoice_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                summary = payment_services.get_payment_summary(cursor, invoice_id=invoice_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving payment summary."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PaymentSummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentDetailView(APIView):
    def get(self, request, payment_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                payment = payment_services.get_payment_by_id(cursor, payment_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving the payment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, payment_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                payment_services.delete_payment(cursor, payment_id=payment_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while deleting the payment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deleting the payment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductListCreateView(APIView):
    def get(self, request):
        active_only = request.query_params.get("active_only", "").lower() in {"1", "true", "yes"}

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                products = product_services.list_products(cursor, active_only=active_only)

        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving products."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                product = product_services.create_product(
                    cursor,
                    name=serializer.validated_data["name"],
                    description=serializer.validated_data.get("description"),
                    unit_price_cents=serializer.validated_data["unit_price_cents"],
                    category_id=serializer.validated_data.get("category_id", 1),
                    is_active=serializer.validated_data.get("is_active", True),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while creating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductDetailView(APIView):
    def get(self, request, product_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                product = product_services.get_product_by_id(cursor, product_id=product_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, product_id):
        serializer = ProductUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                product = product_services.update_product_by_id(
                    cursor,
                    product_id=product_id,
                    name=serializer.validated_data.get("name"),
                    description=serializer.validated_data.get("description"),
                    unit_price_cents=serializer.validated_data.get("unit_price_cents"),
                    category_id=serializer.validated_data.get("category_id"),
                    is_active=serializer.validated_data.get("is_active"),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while updating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while updating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, product_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                product_services.delete_product(cursor, product_id=product_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deleting the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductCategoryListCreateView(APIView):
    def get(self, request):
        active_only = request.query_params.get("active_only", "").lower() in {"1", "true", "yes"}

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                categories = product_category_services.list_product_categories(
                    cursor,
                    active_only=active_only,
                )

        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving product categories."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductCategorySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                category = product_category_services.create_product_category(
                    cursor,
                    name=serializer.validated_data["name"],
                    description=serializer.validated_data.get("description"),
                    is_active=serializer.validated_data.get("is_active", True),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while creating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductCategoryDetailView(APIView):
    def patch(self, request, category_id):
        serializer = ProductCategoryUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                category = product_category_services.update_product_category_by_id(
                    cursor,
                    category_id=category_id,
                    name=serializer.validated_data.get("name"),
                    description=serializer.validated_data.get("description"),
                    is_active=serializer.validated_data.get("is_active"),
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while updating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while updating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductCategoryDeactivateView(APIView):
    def patch(self, request, category_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                category = product_category_services.deactivate_product_category(
                    cursor,
                    category_id=category_id,
                )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while deactivating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deactivating the product category."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductDeactivateView(APIView):
    def patch(self, request, product_id):
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                product = product_services.deactivate_product(cursor, product_id=product_id)

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ServiceError:
            return Response(
                {"detail": "Something went wrong while deactivating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while deactivating the product."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class AssistantQueryView(APIView):
    def post(self, request):
        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with connection.db_session(connection.DB_PATH) as (connect, cursor):
            cursor = connect.cursor()

            customers = list_customers(cursor)
            customer_names = [customer["name"] for customer in customers]

            assistant_intent = router.route(
                message=message,
                customer_names=customer_names,
            )

            data_source = ServiceInvoiceAssistantDataSource(cursor)
            dispatcher = AssistantDispatcher(data_source)
            assistant_response = dispatcher.dispatch(assistant_intent)



        return Response(
            {
                "message": message,
                "assistant_intent": assistant_intent.model_dump(),
                "assistant_response": assistant_response.model_dump(),

            },
            status=status.HTTP_200_OK,
        )
