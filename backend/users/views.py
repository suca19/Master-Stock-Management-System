import logging
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from guardian.conf import settings as guardian_settings
from .serializers import UserSerializer, UserUpdateSerializer, ProfileSerializer
from .permissions import IsAdminUser, IsSelfOrAdmin

logger = logging.getLogger('users')

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing User instances."""
    
    # Hide django-guardian's internal anonymous user
    queryset = User.objects.exclude(email=guardian_settings.ANONYMOUS_USER_NAME)
    serializer_class = UserSerializer
    pagination_class = None
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsSelfOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action in ['update', 'partial_update']:
            # Only admins may change roles; everyone else edits their own profile fields
            if self.request.user.role == User.ADMIN:
                return UserUpdateSerializer
            return ProfileSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(f"User created: {user.id} - {user.email}")
    
    def perform_update(self, serializer):
        user = serializer.save()
        logger.info(f"User updated: {user.id} - {user.email}")
    
    def perform_destroy(self, instance):
        logger.info(f"User deleted: {instance.id} - {instance.email}")
        instance.delete()
    
    @action(detail=False, methods=['get'], url_path='team-members')
    def team_members(self, request):
        """List staff members for supervisors."""
        members = self.get_queryset().filter(role=User.STAFF, is_active=True)
        return Response(UserUpdateSerializer(members, many=True).data)

class ProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's profile."""
    
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangeOwnPasswordView(generics.GenericAPIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password') or request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({"detail": "current_password and new_password are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(current_password):
            return Response({"current_password": ["Wrong password."]},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"new_password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        logger.info(f"Password changed for user: {user.id} - {user.email}")
        return Response({"status": "password changed successfully"})
