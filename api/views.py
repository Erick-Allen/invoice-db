import sqlite3

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from invoice_db.db import connection
from invoice_db.services import customers as customer_services
from invoice_db.services.exceptions import  ValidationError, NotFoundError, ServiceError


from .serializers import CustomerSerializer, CustomerUpdateSerializer

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
                {"detail": "A database error occurred while creating the customer"}
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
                {"detail": "A database error occurred while creating the customer"}
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
                {"detail": "A database error occurred while creating the customer"}
            )
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, customer_id):
        try:
             with connection.db_session(connection.DB_PATH) as (connect, cursor):
                 customer_services.delete_customer_by_id(cursor, customer_id=customer_id)

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
                {"detail": "A database error occurred while creating the customer"}
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)