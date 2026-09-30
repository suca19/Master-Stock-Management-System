from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from inventory.views import (
    CategoryViewSet,
    ProductImageViewSet,
    ProductViewSet,
    StockMovementViewSet,
    SupplierViewSet,
)
from orders.views import OrderViewSet
from users.views import UserViewSet, ProfileView, ChangeOwnPasswordView
from .views import register_user, dashboard_data, CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'stock-movements', StockMovementViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    # Explicit routes go before the router so they aren't matched as detail routes
    path('auth/register/', register_user, name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', ChangeOwnPasswordView.as_view(), name='change_password'),

    path('users/profile/', ProfileView.as_view(), name='user_profile'),
    path('dashboard/data/', dashboard_data, name='dashboard_data'),

    path('', include(router.urls)),
]
