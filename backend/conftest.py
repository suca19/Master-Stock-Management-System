"""Fixtures shared by every app's tests."""
import pytest
from rest_framework.test import APIClient

from inventory.services import record_stock_movement
from inventory.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


@pytest.fixture
def admin_user(db):
    return UserFactory(role=User.ADMIN, is_staff=True, is_superuser=True)


@pytest.fixture
def manager_user(db):
    return UserFactory(role=User.MANAGER)


@pytest.fixture
def staff_user(db):
    return UserFactory(role=User.STAFF)


@pytest.fixture
def api_client():
    return APIClient()


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(admin_user):
    return _client_for(admin_user)


@pytest.fixture
def manager_client(manager_user):
    return _client_for(manager_user)


@pytest.fixture
def staff_client(staff_user):
    return _client_for(staff_user)


@pytest.fixture
def stocked_product(db, admin_user):
    """A product with 10 units in stock, put there through the ledger like real stock."""
    product = ProductFactory()
    record_stock_movement(product=product, quantity=10, movement_type='in', performed_by=admin_user)
    return product
