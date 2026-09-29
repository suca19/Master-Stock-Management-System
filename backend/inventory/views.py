import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import ProtectedError
from .models import Category, Product, ProductImage, Supplier, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer, ProductImageSerializer,
    SupplierSerializer, StockMovementSerializer
)
from users.permissions import IsAdminUser, IsStaffMember, IsWorkerOrAdmin

logger = logging.getLogger('inventory')


class ProtectedDestroyMixin:
    """Answer 409 instead of 500 when a row is still referenced (on_delete=PROTECT)."""

    protected_message = "This record is still in use and can't be deleted."

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"detail": self.protected_message}, status=status.HTTP_409_CONFLICT)

class CategoryViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    """ViewSet for viewing and editing Category instances."""
    
    queryset = Category.objects.all()
    protected_message = "This category still has products. Move or delete them first."
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsWorkerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        """
        Override to ensure only admins can create, update or delete categories.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        category = serializer.save()
        logger.info(f"Category created: {category.id} - {category.name}")
    
    def perform_update(self, serializer):
        category = serializer.save()
        logger.info(f"Category updated: {category.id} - {category.name}")
    
    def perform_destroy(self, instance):
        logger.info(f"Category deleted: {instance.id} - {instance.name}")
        instance.delete()

class ProductViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    """ViewSet for viewing and editing Product instances."""
    
    queryset = Product.objects.select_related('category').prefetch_related('images')
    serializer_class = ProductSerializer
    protected_message = "This product has order or stock history. Set is_active to false instead."
    permission_classes = [IsAuthenticated, IsWorkerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description', 'sku', 'barcode']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    
    def get_permissions(self):
        """
        Override to ensure only admins can create, update or delete products.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        product = serializer.save()
        logger.info(f"Product created: {product.id} - {product.name}")
    
    def perform_update(self, serializer):
        product = serializer.save()
        logger.info(f"Product updated: {product.id} - {product.name}")
    
    def perform_destroy(self, instance):
        logger.info(f"Product deleted: {instance.id} - {instance.name}")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock."""
        products = self.get_queryset().filter(stock__lte=models.F('low_stock_threshold'))
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

class ProductImageViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing ProductImage instances."""
    
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated, IsWorkerOrAdmin]
    
    def get_permissions(self):
        """
        Override to ensure only admins can create, update or delete product images.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # If this is set as primary, unset any existing primary images for this product
        if serializer.validated_data.get('is_primary', False):
            product = serializer.validated_data['product']
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
        
        image = serializer.save()
        logger.info(f"Product image created: {image.id} for product {image.product.name}")

class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Supplier instances."""
    
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsWorkerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        """
        Override to ensure only admins can create, update or delete suppliers.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

class StockMovementViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing StockMovement instances."""
    
    queryset = StockMovement.objects.select_related('product', 'performed_by')
    http_method_names = ['get', 'post', 'head', 'options']  # movements are append-only
    serializer_class = StockMovementSerializer
    # Any internal user can record stock in/out; nobody can edit or delete a movement
    permission_classes = [IsStaffMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type']
    ordering_fields = ['created_at']
    
    def perform_create(self, serializer):
        movement = serializer.save()
        logger.info(f"Stock movement created: {movement.id} - {movement.product.name} ({movement.quantity})")

