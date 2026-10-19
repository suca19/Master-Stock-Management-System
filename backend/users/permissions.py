from rest_framework import permissions

from .models import User

# Everyone who works at the shop and may log in (customers never log in)
INTERNAL_ROLES = frozenset({User.ADMIN, User.MANAGER, User.STAFF})


class HasRole(permissions.BasePermission):
    """
    Base class: allow signed-in users whose role is in `allowed_roles`.

    Subclasses only declare the roles, so every rule is one line and role names
    come from the User constants instead of repeated strings.
    """

    allowed_roles = frozenset()

    def has_permission(self, request, view):
        user = request.user
        # Anonymous users have no `role`; `is_authenticated` is False for them, so we stop there
        return bool(user and user.is_authenticated and user.role in self.allowed_roles)


class IsAdminUser(HasRole):
    """Only admins."""

    allowed_roles = frozenset({User.ADMIN})


class IsWorkerOrAdmin(permissions.BasePermission):
    """
    Permission to allow workers and admins to access the view.
    Workers have read-only access to most resources.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin can do anything
        if request.user.role == "admin":
            return True

        # Workers can only perform safe methods (GET, HEAD, OPTIONS)
        return request.user.role == "staff" and request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.role == "admin":
            return True

        # Workers can only view
        return request.user.role == "staff" and request.method in permissions.SAFE_METHODS


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Permission to only allow users to edit their own profile or admins to edit any profile.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is admin
        if request.user.role == "admin":
            return True

        # Allow if user is editing their own profile
        return obj == request.user


class IsStaffMember(HasRole):
    """Any internal user (admin, manager, staff). Customers and anonymous users are rejected."""

    allowed_roles = INTERNAL_ROLES
