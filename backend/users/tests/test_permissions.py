from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser

from users.permissions import IsAdminUser, IsSelfOrAdmin, IsStaffMember, IsWorkerOrAdmin


def request_for(role=None, method='GET'):
    user = AnonymousUser() if role is None else SimpleNamespace(is_authenticated=True, role=role)
    return SimpleNamespace(user=user, method=method)


@pytest.mark.parametrize('role, allowed', [
    ('admin', True), ('manager', False), ('staff', False), ('customer', False), (None, False),
])
def test_is_admin_user(role, allowed):
    assert bool(IsAdminUser().has_permission(request_for(role), None)) is allowed


@pytest.mark.parametrize('role, allowed', [
    ('admin', True), ('manager', True), ('staff', True), ('customer', False), (None, False),
])
def test_is_staff_member(role, allowed):
    assert bool(IsStaffMember().has_permission(request_for(role), None)) is allowed


@pytest.mark.parametrize('role, method, allowed', [
    ('admin', 'POST', True),
    ('staff', 'GET', True),
    ('staff', 'POST', False),
    ('customer', 'GET', False),
    (None, 'GET', False),
])
def test_is_worker_or_admin(role, method, allowed):
    assert bool(IsWorkerOrAdmin().has_permission(request_for(role, method), None)) is allowed


@pytest.mark.xfail(strict=True, reason='Known issue, fixed in Phase 4: IsWorkerOrAdmin ignores the manager role')
def test_manager_can_read_inventory():
    assert IsWorkerOrAdmin().has_permission(request_for('manager', 'GET'), None)


def test_is_self_or_admin():
    me = SimpleNamespace(id=1, is_authenticated=True, role='staff')
    other = SimpleNamespace(id=2, is_authenticated=True, role='staff')
    admin = SimpleNamespace(id=3, is_authenticated=True, role='admin')
    permission = IsSelfOrAdmin()

    assert permission.has_object_permission(SimpleNamespace(user=me), None, me)
    assert not permission.has_object_permission(SimpleNamespace(user=me), None, other)
    assert permission.has_object_permission(SimpleNamespace(user=admin), None, other)
