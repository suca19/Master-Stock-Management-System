# api/views.py
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from inventory.models import Product
from users.permissions import IsStaffMember

from .serializers import RegisterSerializer, UserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=serializer.context).data,
            "message": "User created successfully",
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsStaffMember])
def dashboard_data(request):
    products = Product.objects.filter(is_active=True)
    stock_value = ExpressionWrapper(F('stock') * F('price'),
                                    output_field=DecimalField(max_digits=14, decimal_places=2))
    return Response({
        'totalProducts': products.count(),
        'lowStockItems': products.filter(stock__lte=F('low_stock_threshold')).count(),
        'totalValue': products.aggregate(total=Sum(stock_value))['total'] or Decimal('0.00'),
    })
