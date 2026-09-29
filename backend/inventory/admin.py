from django.contrib import admin

from .models import Category, Product, ProductImage, StockMovement, Supplier


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'price', 'stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['sku', 'name', 'barcode']
    list_select_related = ['category']
    # Stock only changes through stock movements
    readonly_fields = ['stock', 'created_by', 'created_at', 'updated_at']
    inlines = [ProductImageInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_name', 'email', 'phone', 'is_active']
    search_fields = ['name', 'contact_name', 'email']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'product', 'movement_type', 'quantity', 'reference', 'performed_by']
    list_filter = ['movement_type']
    search_fields = ['product__name', 'product__sku', 'reference']
    list_select_related = ['product', 'performed_by']

    # The ledger is append-only and must go through inventory.services
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
