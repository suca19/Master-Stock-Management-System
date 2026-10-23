from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser

from users.permissions import CatalogPermission, IsAdminUser, IsSelfOrAdmin, IsStaffMember


def request_for(role=None, method="GET"):
    user = AnonymousUser() if role is None else SimpleNamespace(is_authenticated=True, role=role)
    return SimpleNamespace(user=user, method=method)


@pytest.mark.parametrize(
    "role, allowed",
    [
        ("admin", True),
        ("manager", False),
        ("staff", False),
        ("customer", False),
        (None, False),
    ],
)
def test_is_admin_user(role, allowed):
    assert bool(IsAdminUser().has_permission(request_for(role), None)) is allowed


@pytest.mark.parametrize(
    "role, allowed",
    [
        ("admin", True),
        ("manager", True),
        ("staff", True),
        ("customer", False),
        (None, False),
    ],
)
def test_is_staff_member(role, allowed):
    assert bool(IsStaffMember().has_permission(request_for(role), None)) is allowed


@pytest.mark.parametrize(
    "role, method, allowed",
    [
        ("admin", "POST", True),
        ("manager", "GET", True),  # was the Phase 3 bug: managers couldn't even read
        ("manager", "DELETE", True),
        ("staff", "GET", True),
        ("staff", "POST", False),
        ("staff", "PATCH", False),
        ("customer", "GET", False),
        (None, "GET", False),
    ],
)
def test_catalog_permission(role, method, allowed):
    assert CatalogPermission().has_permission(request_for(role, method), None) is allowed


def test_is_self_or_admin():
    me = SimpleNamespace(id=1, is_authenticated=True, role="staff")
    other = SimpleNamespace(id=2, is_authenticated=True, role="staff")
    admin = SimpleNamespace(id=3, is_authenticated=True, role="admin")
    permission = IsSelfOrAdmin()

    assert permission.has_object_permission(SimpleNamespace(user=me), None, me)
    assert not permission.has_object_permission(SimpleNamespace(user=me), None, other)
    assert permission.has_object_permission(SimpleNamespace(user=admin), None, other)
