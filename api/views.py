import sqlite3

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from invoice_db.db import connection
from invoice_db.services import customers as customer_services
from invoice_db.services import invoices as invoice_services
from invoice_db.services.exceptions import  ValidationError, NotFoundError, ServiceError
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
    InvoiceStatusUpdateSerializer
)

@api_view(["GET"])
def api_root(request):
    return Response(
        {
            "message": "Invoice DB API",
            "endpoints": {
                "customers": "/api/customers/",
                "invoices": "/api/invoices",
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
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoices = invoice_services.list_invoices(cursor=cursor)

        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while retrieving invoices."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
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
                    total=serializer.validated_data['total'],
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
        try:
            with connection.db_session(connection.DB_PATH) as (connect, cursor):
                invoice = invoice_services.get_invoice_by_id(
                    cursor=cursor,
                    invoice_id=invoice_id
                )

        except NotFoundError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        except sqlite3.Error:
            return Response(
                {"detail": "A database error occurred while creating the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
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
                    new_total=serializer.validated_data.get("total"),
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
    
router = AssistantRouter(use_qwen=False)

    
class AssistantQueryView(APIView):
    def post(self, request):
        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with get_connection(connection.DB_PATH) as conn:
            cursor = conn.cursor()

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