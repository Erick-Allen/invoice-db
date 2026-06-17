from rest_framework import serializers
from invoice_db.services.invoices import VALID_INVOICE_STATUSES
from invoice_db import utils

class StrictSerializer(serializers.Serializer):
    def validate(self, attrs):
        allowed_fields = set(self.fields.keys())
        received_fields = set(self.initial_data.keys())
        unknown_fields = received_fields - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {
                    "detail": f"Unknown field(s): {', '.join(sorted(unknown_fields))}"
                }
            )
        return attrs

class CustomerSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=255)

class CustomerUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=50, required=False)
    email = serializers.EmailField(max_length=255, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )
        
        return attrs
    
class InvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField()
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)
    total = serializers.IntegerField()
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)

class InvoiceCreateSerializer(StrictSerializer):
    customer_id = serializers.IntegerField()
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)

class InvoiceUpdateSerializer(StrictSerializer):
    customer_id = serializers.IntegerField(required=False)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )
        
        return attrs
    
class InvoiceStatusUpdateSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)

class InvoiceItemSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    invoice_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price_cents = serializers.IntegerField(min_value=0)
    line_total_cents = serializers.IntegerField(read_only=True)

class InvoiceItemCreateSerializer(StrictSerializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False, allow_null=True)

class InvoiceItemUpdateSerializer(StrictSerializer):
    product_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class ProductSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_price_cents = serializers.IntegerField(min_value=0)
    is_active = serializers.BooleanField(required=False, default=True)

class ProductUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs
