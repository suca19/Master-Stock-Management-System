from rest_framework import serializers

from inventory.models import Product

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'unit_price', 'quantity', 'line_total']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_email', 'customer_phone', 'notes',
                  'status', 'subtotal', 'total', 'items',
                  'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'subtotal', 'total', 'created_by', 'created_at', 'updated_at']

    def validate_status(self, value):
        if value == Order.Status.CANCELLED:
            raise serializers.ValidationError("Use the cancel action to cancel an order.")
        if self.instance and self.instance.status == Order.Status.CANCELLED:
            raise serializers.ValidationError("A cancelled order can't change status.")
        return value


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False, allow_blank=True, default='')
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        product_ids = [item['product'].pk for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Each product can only appear once per order.")
        return items
