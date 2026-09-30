import logging

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from inventory.services import InsufficientStock
from users.permissions import IsStaffMember

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from .services import OrderError, cancel_order, place_order

logger = logging.getLogger('orders')


class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders recorded by staff for customers. Orders are never deleted:
    cancel them instead, which puts the stock back.
    """

    queryset = Order.objects.select_related('created_by').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [IsStaffMember]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['customer_name', 'customer_email', 'customer_phone']
    ordering_fields = ['created_at', 'total']

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = place_order(created_by=request.user, **serializer.validated_data)
        except (OrderError, InsufficientStock) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Order created: {order.pk} by user {request.user.pk}")
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        try:
            order = cancel_order(self.get_object(), performed_by=request.user)
        except OrderError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Order cancelled: {order.pk} by user {request.user.pk}")
        return Response(OrderSerializer(order).data)
