import pytest

from inventory.models import Product, StockMovement
from inventory.tests.factories import CategoryFactory, ProductFactory

pytestmark = pytest.mark.django_db


class TestProductApi:
    def test_admin_creates_product_and_is_recorded_as_creator(self, admin_client, admin_user):
        category = CategoryFactory()
        response = admin_client.post('/api/products/', {
            'sku': 'NEW-1', 'name': 'Keyboard', 'category': category.id,
            'price': '30.00', 'cost_price': '12.00',
        }, format='json')

        assert response.status_code == 201
        assert Product.objects.get(sku='NEW-1').created_by == admin_user

    def test_stock_cannot_be_set_directly(self, admin_client):
        category = CategoryFactory()
        response = admin_client.post('/api/products/', {
            'sku': 'NEW-2', 'name': 'Mouse', 'category': category.id,
            'price': '10.00', 'cost_price': '4.00', 'stock': 999,
        }, format='json')

        assert response.status_code == 201
        assert response.data['stock'] == 0

    def test_staff_can_read_but_not_create(self, staff_client):
        ProductFactory()
        assert staff_client.get('/api/products/').status_code == 200

        response = staff_client.post('/api/products/', {'sku': 'X', 'name': 'X'}, format='json')
        assert response.status_code == 403

    def test_anonymous_is_rejected(self, api_client):
        assert api_client.get('/api/products/').status_code == 401

    def test_low_stock_lists_only_low_products(self, admin_client):
        low = ProductFactory(stock=2, low_stock_threshold=5)
        ProductFactory(stock=50, low_stock_threshold=5)

        response = admin_client.get('/api/products/low_stock/')
        assert [p['id'] for p in response.data] == [low.id]

    def test_search_by_sku(self, admin_client):
        ProductFactory(sku='FIND-ME')
        ProductFactory(sku='OTHER')

        response = admin_client.get('/api/products/?search=FIND')
        assert [p['sku'] for p in response.data['results']] == ['FIND-ME']

    def test_deleting_product_with_history_returns_409(self, admin_client, stocked_product):
        response = admin_client.delete(f'/api/products/{stocked_product.id}/')

        assert response.status_code == 409
        assert 'is_active' in response.data['detail']
        assert Product.objects.filter(pk=stocked_product.pk).exists()

    def test_deleting_unused_product_works(self, admin_client):
        product = ProductFactory()
        assert admin_client.delete(f'/api/products/{product.id}/').status_code == 204


class TestCategoryApi:
    def test_deleting_category_with_products_returns_409(self, admin_client):
        product = ProductFactory()
        response = admin_client.delete(f'/api/categories/{product.category_id}/')
        assert response.status_code == 409


class TestStockMovementApi:
    def test_staff_records_stock_in(self, staff_client, staff_user):
        product = ProductFactory()
        response = staff_client.post('/api/stock-movements/', {
            'product': product.id, 'quantity': 5, 'movement_type': 'in',
        }, format='json')

        assert response.status_code == 201
        product.refresh_from_db()
        assert product.stock == 5
        assert StockMovement.objects.get().performed_by == staff_user

    @pytest.mark.parametrize('movement_type, quantity', [('in', -5), ('out', 5), ('adjustment', 0)])
    def test_rejects_wrong_sign(self, staff_client, stocked_product, movement_type, quantity):
        response = staff_client.post('/api/stock-movements/', {
            'product': stocked_product.id, 'quantity': quantity, 'movement_type': movement_type,
        }, format='json')
        assert response.status_code == 400

    def test_rejects_stock_out_beyond_available(self, staff_client, stocked_product):
        response = staff_client.post('/api/stock-movements/', {
            'product': stocked_product.id, 'quantity': -11, 'movement_type': 'out',
        }, format='json')

        assert response.status_code == 400
        stocked_product.refresh_from_db()
        assert stocked_product.stock == 10

    def test_movements_cannot_be_edited_or_deleted(self, admin_client, stocked_product):
        movement = stocked_product.stock_movements.get()
        url = f'/api/stock-movements/{movement.id}/'

        assert admin_client.patch(url, {'quantity': 99}, format='json').status_code == 405
        assert admin_client.delete(url).status_code == 405
