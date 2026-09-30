from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from inventory.tests.factories import ProductFactory
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

URL = '/api/dashboard/data/'


def test_totals_count_active_products_only(staff_client):
    ProductFactory(stock=10, price=Decimal('2.50'), low_stock_threshold=5)   # value 25.00
    ProductFactory(stock=3, price=Decimal('10.00'), low_stock_threshold=5)   # value 30.00, low stock
    ProductFactory(stock=100, price=Decimal('1.00'), is_active=False)         # ignored

    data = staff_client.get(URL).data

    assert data['totalProducts'] == 2
    assert data['lowStockItems'] == 1
    assert Decimal(str(data['totalValue'])) == Decimal('55.00')


def test_empty_inventory(staff_client):
    data = staff_client.get(URL).data
    assert data == {'totalProducts': 0, 'lowStockItems': 0, 'totalValue': Decimal('0.00')}


def test_customers_and_anonymous_are_rejected(api_client):
    assert api_client.get(URL).status_code == 401

    client = APIClient()
    client.force_authenticate(UserFactory(role='customer'))
    assert client.get(URL).status_code == 403
