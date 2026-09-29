import pytest

from inventory.models import StockMovement
from inventory.services import InsufficientStock, record_stock_movement
from inventory.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_stock_in_increases_stock_and_records_movement(admin_user):
    product = ProductFactory(stock=0)

    movement = record_stock_movement(product=product, quantity=7, movement_type='in',
                                     performed_by=admin_user, reference='PO-42')

    product.refresh_from_db()
    assert product.stock == 7
    assert movement.quantity == 7
    assert movement.performed_by == admin_user
    assert movement.reference == 'PO-42'


def test_stock_out_decreases_stock(stocked_product):
    record_stock_movement(product=stocked_product, quantity=-4, movement_type='out')
    stocked_product.refresh_from_db()
    assert stocked_product.stock == 6


def test_callers_instance_is_kept_in_sync(stocked_product):
    record_stock_movement(product=stocked_product, quantity=-1, movement_type='out')
    assert stocked_product.stock == 9  # no refresh_from_db needed


def test_cannot_take_more_than_available(stocked_product):
    with pytest.raises(InsufficientStock) as exc:
        record_stock_movement(product=stocked_product, quantity=-11, movement_type='out')

    assert '10 available' in str(exc.value)
    stocked_product.refresh_from_db()
    assert stocked_product.stock == 10
    # Only the initial stock-in exists; the failed movement left no trace
    assert StockMovement.objects.filter(product=stocked_product).count() == 1


def test_can_take_exactly_all_stock(stocked_product):
    record_stock_movement(product=stocked_product, quantity=-10, movement_type='out')
    stocked_product.refresh_from_db()
    assert stocked_product.stock == 0


def test_negative_adjustment_is_applied(stocked_product):
    record_stock_movement(product=stocked_product, quantity=-3, movement_type='adjustment', notes='damaged')
    stocked_product.refresh_from_db()
    assert stocked_product.stock == 7


def test_stock_equals_sum_of_ledger(stocked_product):
    for quantity, kind in [(5, 'in'), (-8, 'out'), (2, 'return'), (-1, 'adjustment')]:
        record_stock_movement(product=stocked_product, quantity=quantity, movement_type=kind)

    stocked_product.refresh_from_db()
    ledger_total = sum(m.quantity for m in stocked_product.stock_movements.all())
    assert stocked_product.stock == ledger_total == 8
