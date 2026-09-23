from rest_framework import serializers
from invoice_db.db.payments import VALID_PAYMENT_METHODS
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
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_type = serializers.CharField(required=False)
    company_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

class CustomerUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=50, required=False)
    email = serializers.EmailField(max_length=255, required=False)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_type = serializers.CharField(required=False)
    company_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

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
    location_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)
    total = serializers.IntegerField()
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)

class InvoiceCreateSerializer(StrictSerializer):
    customer_id = serializers.IntegerField()
    location_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)

class InvoiceUpdateSerializer(StrictSerializer):
    customer_id = serializers.IntegerField(required=False)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )
        
        return attrs

class CustomerLocationSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    location_id = serializers.IntegerField(read_only=True)
    label = serializers.CharField(max_length=255)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=32)
    country = serializers.CharField(max_length=64, required=False, default="US")
    is_primary = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class CustomerLocationUpdateSerializer(StrictSerializer):
    label = serializers.CharField(max_length=255, required=False)
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255, required=False)
    state = serializers.CharField(max_length=255, required=False)
    postal_code = serializers.CharField(max_length=32, required=False)
    country = serializers.CharField(max_length=64, required=False)
    is_primary = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class SupplierLocationSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    supplier_id = serializers.IntegerField(read_only=True)
    location_id = serializers.IntegerField(read_only=True)
    label = serializers.CharField(max_length=255)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=32)
    country = serializers.CharField(max_length=64, required=False, default="US")
    is_primary = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class SupplierLocationUpdateSerializer(StrictSerializer):
    label = serializers.CharField(max_length=255, required=False)
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255, required=False)
    state = serializers.CharField(max_length=255, required=False)
    postal_code = serializers.CharField(max_length=32, required=False)
    country = serializers.CharField(max_length=64, required=False)
    is_primary = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class LocationSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=32)
    country = serializers.CharField(max_length=64)
    assigned_customer_count = serializers.IntegerField(read_only=True)
    assigned_customer_names = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_supplier_count = serializers.IntegerField(read_only=True)
    assigned_supplier_names = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_count = serializers.IntegerField(read_only=True)
    assigned_names = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class LocationCreateSerializer(StrictSerializer):
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=32)
    country = serializers.CharField(max_length=64, required=False, default="US")

class LocationUpdateSerializer(StrictSerializer):
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255, required=False)
    state = serializers.CharField(max_length=255, required=False)
    postal_code = serializers.CharField(max_length=32, required=False)
    country = serializers.CharField(max_length=64, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class LocationCustomerAssignmentSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    customer_email = serializers.EmailField(read_only=True)
    label = serializers.CharField(read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class LocationSupplierAssignmentSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    supplier_id = serializers.IntegerField(read_only=True)
    supplier_name = serializers.CharField(read_only=True)
    supplier_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    supplier_email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    label = serializers.CharField(read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class LocationInvoiceSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    customer_location_id = serializers.IntegerField(read_only=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)
    total = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)

class LocationDetailSerializer(StrictSerializer):
    location = LocationSerializer(read_only=True)
    customer_assignments = LocationCustomerAssignmentSerializer(many=True, read_only=True)
    supplier_assignments = LocationSupplierAssignmentSerializer(many=True, read_only=True)
    invoices = LocationInvoiceSerializer(many=True, read_only=True)
    
class InvoiceStatusUpdateSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)

class InvoiceItemSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    invoice_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_cost_cents = serializers.IntegerField(min_value=0)
    cost_total_cents = serializers.IntegerField(read_only=True)
    unit_price_cents = serializers.IntegerField(min_value=0)
    line_total_cents = serializers.IntegerField(read_only=True)
    profit_total_cents = serializers.IntegerField(read_only=True)

class InvoiceItemCreateSerializer(StrictSerializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    unit_cost_cents = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False, allow_null=True)

class InvoiceItemUpdateSerializer(StrictSerializer):
    product_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)
    unit_cost_cents = serializers.IntegerField(min_value=0, required=False)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class PaymentSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    invoice_id = serializers.IntegerField()
    amount_cents = serializers.IntegerField(min_value=1)
    payment_date = serializers.DateField()
    method = serializers.ChoiceField(choices=sorted(VALID_PAYMENT_METHODS))
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PaymentCreateSerializer(StrictSerializer):
    amount_cents = serializers.IntegerField(min_value=1)
    payment_date = serializers.DateField()
    method = serializers.ChoiceField(choices=sorted(VALID_PAYMENT_METHODS))
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PaymentSummarySerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    invoice_total_cents = serializers.IntegerField()
    amount_paid_cents = serializers.IntegerField()
    balance_due_cents = serializers.IntegerField()
    is_paid = serializers.BooleanField()

class ProductSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    cost_cents = serializers.IntegerField(min_value=0, required=False, default=0)
    unit_price_cents = serializers.IntegerField(min_value=0)
    category_id = serializers.IntegerField(min_value=1, required=False, default=1)
    category_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(required=False, default=True)
    product_supplier_count = serializers.IntegerField(read_only=True)
    invoice_item_count = serializers.IntegerField(read_only=True)

class ProductUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    cost_cents = serializers.IntegerField(min_value=0, required=False)
    unit_price_cents = serializers.IntegerField(min_value=0, required=False)
    category_id = serializers.IntegerField(min_value=1, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class SupplierSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

class SupplierUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class ProductSupplierSerializer(StrictSerializer):
    product_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

class ProductSupplierCreateSerializer(StrictSerializer):
    supplier_id = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class ProductSupplierUpdateSerializer(StrictSerializer):
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class ProductCategorySerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

class ProductCategoryUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class ProductCategoryMetricsSerializer(serializers.Serializer):
    product_count = serializers.IntegerField()
    active_product_count = serializers.IntegerField()
    invoice_count = serializers.IntegerField()
    revenue_total_cents = serializers.IntegerField()
    cost_total_cents = serializers.IntegerField()
    profit_total_cents = serializers.IntegerField()

class ProductCategoryInvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)
    revenue_total_cents = serializers.IntegerField(read_only=True)
    cost_total_cents = serializers.IntegerField(read_only=True)
    profit_total_cents = serializers.IntegerField(read_only=True)

class ProductCategoryDetailSerializer(serializers.Serializer):
    category = ProductCategorySerializer(read_only=True)
    metrics = ProductCategoryMetricsSerializer(read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    invoices = ProductCategoryInvoiceSerializer(many=True, read_only=True)

class TagSerializer(StrictSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

class TagUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )

        return attrs

class TagMetricsSerializer(serializers.Serializer):
    invoice_count = serializers.IntegerField()
    issued_invoice_count = serializers.IntegerField()
    total_invoiced_cents = serializers.IntegerField()
    total_cost_cents = serializers.IntegerField()
    total_paid_cents = serializers.IntegerField()
    net_profit_cents = serializers.IntegerField()
    total_owed_cents = serializers.IntegerField()

class TagInvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    date_issued = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField(required=False, allow_null=True)
    total = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=VALID_INVOICE_STATUSES)
    cost_total_cents = serializers.IntegerField(read_only=True)
    amount_paid_cents = serializers.IntegerField(read_only=True)
    balance_due_cents = serializers.IntegerField(read_only=True)

class TagDetailSerializer(serializers.Serializer):
    tag = TagSerializer(read_only=True)
    metrics = TagMetricsSerializer(read_only=True)
    invoices = TagInvoiceSerializer(many=True, read_only=True)

class InvoiceTagSerializer(StrictSerializer):
    invoice_id = serializers.IntegerField()
    tag_id = serializers.IntegerField()
    created_at = serializers.CharField(read_only=True)

class InvoiceTagCreateSerializer(StrictSerializer):
    tag_id = serializers.IntegerField(min_value=1)
