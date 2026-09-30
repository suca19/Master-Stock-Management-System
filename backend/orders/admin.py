from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'unit_price', 'quantity']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'status', 'total', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_email']
    list_select_related = ['created_by']
    readonly_fields = ['subtotal', 'total', 'created_by', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        # Orders must go through orders.services.place_order to take stock out
        return False
