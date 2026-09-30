import pytest
from rest_framework.test import APIClient

from orders.models import Order
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def order_payload(product, quantity=2, **extra):
    return {'customer_name': 'Jane Customer', 'customer_email': 'jane@example.com',
            'items': [{'product': product.id, 'quantity': quantity}], **extra}


class TestCreateOrder:
    def test_staff_places_order(self, staff_client, staff_user, stocked_product):
        response = staff_client.post('/api/orders/', order_payload(stocked_product), format='json')

        assert response.status_code == 201
        assert response.data['total'] == '20.00'
        assert response.data['created_by'] == staff_user.id
        assert response.data['items'][0]['line_total'] == '20.00'

    def test_client_sent_total_is_ignored(self, staff_client, stocked_product):
        response = staff_client.post('/api/orders/', order_payload(stocked_product, total='0.01'), format='json')
        assert response.data['total'] == '20.00'

    def test_rejects_quantity_beyond_stock(self, staff_client, stocked_product):
        response = staff_client.post('/api/orders/', order_payload(stocked_product, quantity=11), format='json')

        assert response.status_code == 400
        assert 'Not enough stock' in response.data['detail']
        assert Order.objects.count() == 0

    def test_rejects_duplicate_product_lines(self, staff_client, stocked_product):
        payload = order_payload(stocked_product)
        payload['items'] *= 2
        assert staff_client.post('/api/orders/', payload, format='json').status_code == 400

    @pytest.mark.parametrize('items', [[], [{'quantity': 1}], [{'product': 999999, 'quantity': 1}]])
    def test_rejects_invalid_items(self, staff_client, items):
        response = staff_client.post('/api/orders/', {'customer_name': 'Jane', 'items': items}, format='json')
        assert response.status_code == 400

    def test_rejects_zero_quantity(self, staff_client, stocked_product):
        response = staff_client.post('/api/orders/', order_payload(stocked_product, quantity=0), format='json')
        assert response.status_code == 400

    def test_customer_role_is_rejected(self, stocked_product):
        client = APIClient()
        client.force_authenticate(UserFactory(role='customer'))
        assert client.post('/api/orders/', order_payload(stocked_product), format='json').status_code == 403

    def test_anonymous_is_rejected(self, api_client, stocked_product):
        assert api_client.post('/api/orders/', order_payload(stocked_product), format='json').status_code == 401


class TestUpdateAndCancel:
    @pytest.fixture
    def order(self, staff_client, stocked_product):
        response = staff_client.post('/api/orders/', order_payload(stocked_product, quantity=3), format='json')
        return Order.objects.get(pk=response.data['id'])

    def test_status_can_move_forward(self, staff_client, order):
        response = staff_client.patch(f'/api/orders/{order.id}/', {'status': 'processing'}, format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'processing'

    def test_totals_are_read_only(self, staff_client, order):
        staff_client.patch(f'/api/orders/{order.id}/', {'total': '1.00'}, format='json')
        order.refresh_from_db()
        assert str(order.total) == '30.00'

    def test_cannot_cancel_through_patch(self, staff_client, order):
        response = staff_client.patch(f'/api/orders/{order.id}/', {'status': 'cancelled'}, format='json')
        assert response.status_code == 400

    def test_cancel_action_returns_stock(self, staff_client, order, stocked_product):
        response = staff_client.post(f'/api/orders/{order.id}/cancel/')

        assert response.status_code == 200
        assert response.data['status'] == 'cancelled'
        stocked_product.refresh_from_db()
        assert stocked_product.stock == 10

    def test_cancelled_order_cannot_change_status(self, staff_client, order):
        staff_client.post(f'/api/orders/{order.id}/cancel/')
        response = staff_client.patch(f'/api/orders/{order.id}/', {'status': 'shipped'}, format='json')
        assert response.status_code == 400

    def test_cancel_twice_is_400(self, staff_client, order):
        staff_client.post(f'/api/orders/{order.id}/cancel/')
        assert staff_client.post(f'/api/orders/{order.id}/cancel/').status_code == 400

    def test_orders_cannot_be_deleted(self, admin_client, order):
        assert admin_client.delete(f'/api/orders/{order.id}/').status_code == 405


class TestListOrders:
    def test_filter_by_status_and_search_customer(self, staff_client, stocked_product):
        staff_client.post('/api/orders/', order_payload(stocked_product, quantity=1), format='json')
        staff_client.post('/api/orders/', {**order_payload(stocked_product, quantity=1),
                                          'customer_name': 'Bob Other'}, format='json')

        assert staff_client.get('/api/orders/?status=pending').data['count'] == 2
        assert staff_client.get('/api/orders/?status=shipped').data['count'] == 0
        results = staff_client.get('/api/orders/?search=Bob').data['results']
        assert [o['customer_name'] for o in results] == ['Bob Other']
