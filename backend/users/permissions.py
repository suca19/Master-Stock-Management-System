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

    def roles_for(self, request):
        """The roles allowed for this request. Override to vary them, e.g. by HTTP method."""
        return self.allowed_roles

    def has_permission(self, request, view):
        user = request.user
        # Anonymous users have no `role`; `is_authenticated` is False for them, so we stop there
        return bool(user and user.is_authenticated and user.role in self.roles_for(request))


class IsAdminUser(HasRole):
    """Only admins."""

    allowed_roles = frozenset({User.ADMIN})


class ReadWriteRoles(HasRole):
    """
    One set of roles may read (GET, HEAD, OPTIONS); another set may also write.

    Subclasses set `read_roles` and `write_roles`.
    """

    read_roles = frozenset()
    write_roles = frozenset()

    def roles_for(self, request):
        if request.method in permissions.SAFE_METHODS:
            return self.read_roles
        return self.write_roles


class CatalogPermission(ReadWriteRoles):
    """Categories, products, images, suppliers: the whole shop reads, admins and managers edit."""

    read_roles = INTERNAL_ROLES
    write_roles = frozenset({User.ADMIN, User.MANAGER})


class IsSelfOrAdmin(permissions.BasePermission):
    """Object-level: admins may edit any user; everyone else only themselves."""

    def has_object_permission(self, request, view, obj):
        return request.user.role == User.ADMIN or obj == request.user


class IsStaffMember(HasRole):
    """Any internal user (admin, manager, staff). Customers and anonymous users are rejected."""

    allowed_roles = INTERNAL_ROLES


class IsAdminOrManager(HasRole):
    """People who manage the team: they may see every user account."""

    allowed_roles = frozenset({User.ADMIN, User.MANAGER})
