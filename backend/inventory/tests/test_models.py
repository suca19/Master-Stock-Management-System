from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from inventory.models import Category, StockMovement
from inventory.tests.factories import CategoryFactory, ProductFactory

pytestmark = pytest.mark.django_db


class TestCategory:
    def test_slug_is_generated_from_name(self):
        category = Category.objects.create(name='Office Supplies')
        assert category.slug == 'office-supplies'

    def test_explicit_slug_is_kept(self):
        category = Category.objects.create(name='Office Supplies', slug='office')
        assert category.slug == 'office'


class TestProduct:
    def test_is_low_stock_at_or_below_threshold(self):
        product = ProductFactory(stock=5, low_stock_threshold=5)
        assert product.is_low_stock
        product.stock = 6
        assert not product.is_low_stock

    def test_profit_margin_is_percentage_of_price(self):
        product = ProductFactory(price=Decimal('25.00'), cost_price=Decimal('10.00'))
        assert product.profit_margin == Decimal('60')

    def test_profit_margin_is_none_for_free_product(self):
        product = ProductFactory(price=Decimal('0.00'), cost_price=Decimal('0.00'))
        assert product.profit_margin is None

    def test_sku_must_be_unique(self):
        ProductFactory(sku='DUP-1')
        with pytest.raises(IntegrityError), transaction.atomic():
            ProductFactory(sku='DUP-1')

    def test_database_rejects_negative_price(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            ProductFactory(price=Decimal('-1.00'))

    def test_database_rejects_negative_cost(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            ProductFactory(cost_price=Decimal('-1.00'))

    def test_category_with_products_cannot_be_deleted(self):
        category = CategoryFactory()
        ProductFactory(category=category)
        with pytest.raises(ProtectedError):
            category.delete()


class TestStockMovement:
    @pytest.mark.parametrize('movement_type, quantity', [
        ('in', 5), ('return', 5), ('out', -5), ('adjustment', 3), ('adjustment', -3),
    ])
    def test_database_accepts_matching_sign(self, movement_type, quantity):
        StockMovement.objects.create(product=ProductFactory(), movement_type=movement_type, quantity=quantity)

    @pytest.mark.parametrize('movement_type, quantity', [
        ('in', -5), ('in', 0), ('return', -1), ('out', 5), ('out', 0), ('adjustment', 0),
    ])
    def test_database_rejects_wrong_sign(self, movement_type, quantity):
        with pytest.raises(IntegrityError), transaction.atomic():
            StockMovement.objects.create(product=ProductFactory(), movement_type=movement_type, quantity=quantity)

    def test_movements_are_immutable(self):
        movement = StockMovement.objects.create(product=ProductFactory(), movement_type='in', quantity=5)
        movement.quantity = 50
        with pytest.raises(ValueError, match='immutable'):
            movement.save()

    def test_str_shows_signed_quantity(self):
        movement = StockMovement.objects.create(product=ProductFactory(), movement_type='out', quantity=-2)
        assert '-2' in str(movement)
