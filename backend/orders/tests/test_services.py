import threading
from decimal import Decimal

import pytest
from django.db import connection

from inventory.models import Product, StockMovement
from inventory.services import InsufficientStock, record_stock_movement
from inventory.tests.factories import ProductFactory
from orders.models import Order
from orders.services import OrderError, cancel_order, place_order


def stock(product, quantity, user=None):
    record_stock_movement(product=product, quantity=quantity, movement_type='in', performed_by=user)
    return product


@pytest.mark.django_db
class TestPlaceOrder:
    def test_creates_order_with_lines_and_server_side_total(self, staff_user):
        mouse = stock(ProductFactory(price=Decimal('25.00')), 10)
        cable = stock(ProductFactory(price=Decimal('4.50')), 10)

        order = place_order(created_by=staff_user, customer_name='Jane', items=[
            {'product': mouse, 'quantity': 2},
            {'product': cable, 'quantity': 3},
        ])

        assert order.status == Order.Status.PENDING
        assert order.created_by == staff_user
        assert order.items.count() == 2
        assert order.subtotal == order.total == Decimal('63.50')  # 2×25 + 3×4.50

    def test_takes_stock_out_and_records_movements(self, staff_user, stocked_product):
        order = place_order(created_by=staff_user, customer_name='Jane',
                            items=[{'product': stocked_product, 'quantity': 4}])

        stocked_product.refresh_from_db()
        assert stocked_product.stock == 6
        movement = StockMovement.objects.get(movement_type='out')
        assert movement.quantity == -4
        assert movement.reference == f'Order #{order.pk}'
        assert movement.performed_by == staff_user

    def test_snapshots_name_and_price(self, staff_user, stocked_product):
        order = place_order(created_by=staff_user, customer_name='Jane',
                            items=[{'product': stocked_product, 'quantity': 1}])
        original_name, original_price = stocked_product.name, stocked_product.price

        Product.objects.filter(pk=stocked_product.pk).update(name='Renamed', price=Decimal('99.00'))

        line = order.items.get()
        assert line.product_name == original_name
        assert line.unit_price == original_price
        order.refresh_from_db()
        assert order.total == original_price

    def test_is_all_or_nothing_when_one_item_lacks_stock(self, staff_user):
        plenty = stock(ProductFactory(), 10)
        scarce = stock(ProductFactory(), 1)

        with pytest.raises(InsufficientStock):
            place_order(created_by=staff_user, customer_name='Jane', items=[
                {'product': plenty, 'quantity': 5},
                {'product': scarce, 'quantity': 2},
            ])

        assert Order.objects.count() == 0
        plenty.refresh_from_db()
        assert plenty.stock == 10  # the first line's stock-out was rolled back

    def test_rejects_empty_order(self, staff_user):
        with pytest.raises(OrderError):
            place_order(created_by=staff_user, customer_name='Jane', items=[])

    def test_rejects_inactive_product(self, staff_user, stocked_product):
        stocked_product.is_active = False
        stocked_product.save()

        with pytest.raises(OrderError, match='no longer available'):
            place_order(created_by=staff_user, customer_name='Jane',
                        items=[{'product': stocked_product, 'quantity': 1}])
        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestCancelOrder:
    def _order(self, user, product, quantity=3):
        return place_order(created_by=user, customer_name='Jane',
                           items=[{'product': product, 'quantity': quantity}])

    def test_returns_stock_and_marks_cancelled(self, staff_user, stocked_product):
        order = self._order(staff_user, stocked_product)

        cancel_order(order, performed_by=staff_user)

        order.refresh_from_db()
        stocked_product.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        assert stocked_product.stock == 10
        assert StockMovement.objects.filter(movement_type='return', quantity=3).exists()

    def test_cannot_cancel_twice(self, staff_user, stocked_product):
        order = self._order(staff_user, stocked_product)
        cancel_order(order, performed_by=staff_user)

        with pytest.raises(OrderError, match='already cancelled'):
            cancel_order(order, performed_by=staff_user)
        stocked_product.refresh_from_db()
        assert stocked_product.stock == 10  # not returned twice

    @pytest.mark.parametrize('status', [Order.Status.SHIPPED, Order.Status.DELIVERED])
    def test_cannot_cancel_after_shipping(self, staff_user, stocked_product, status):
        order = self._order(staff_user, stocked_product)
        Order.objects.filter(pk=order.pk).update(status=status)

        with pytest.raises(OrderError):
            cancel_order(order, performed_by=staff_user)


@pytest.mark.django_db(transaction=True)
def test_concurrent_orders_cannot_oversell(staff_user):
    """Two orders race for 3 units each when only 5 exist: exactly one may win."""
    product = stock(ProductFactory(), 5)
    barrier = threading.Barrier(2)
    results = []

    def attempt():
        try:
            barrier.wait()
            place_order(created_by=staff_user, customer_name='Racer',
                        items=[{'product': Product.objects.get(pk=product.pk), 'quantity': 3}])
            results.append('placed')
        except InsufficientStock:
            results.append('rejected')
        finally:
            connection.close()  # each thread has its own DB connection

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ['placed', 'rejected']
    product.refresh_from_db()
    assert product.stock == 2
