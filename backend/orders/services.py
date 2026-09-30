from decimal import Decimal

from django.db import transaction

from inventory.models import StockMovement
from inventory.services import record_stock_movement

from .models import Order, OrderItem


class OrderError(Exception):
    pass


@transaction.atomic
def place_order(*, created_by, customer_name, items, customer_email="", customer_phone="", notes=""):
    """
    Create an order, take the stock out, and snapshot names and prices.

    `items` is a list of {"product": Product, "quantity": int}. Everything
    happens in one transaction: if any product lacks stock, nothing is saved.
    """
    if not items:
        raise OrderError("An order needs at least one item.")

    order = Order.objects.create(
        created_by=created_by,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        notes=notes,
    )

    subtotal = Decimal("0.00")
    # Lock products in a consistent order so concurrent orders can't deadlock
    for item in sorted(items, key=lambda i: i["product"].pk):
        if not item["product"].is_active:
            raise OrderError(f"{item['product'].name} is no longer available.")

        movement = record_stock_movement(
            product=item["product"],
            quantity=-item["quantity"],
            movement_type=StockMovement.MovementType.OUT,
            performed_by=created_by,
            reference=f"Order #{order.pk}",
        )
        product = movement.product  # the locked, up-to-date row

        line = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=item["quantity"],
        )
        subtotal += line.line_total

    order.subtotal = subtotal
    order.total = subtotal
    order.save(update_fields=["subtotal", "total", "updated_at"])
    return order


@transaction.atomic
def cancel_order(order, *, performed_by):
    """Cancel an order and put its items back into stock."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.CANCELLED:
        raise OrderError("This order is already cancelled.")
    if order.status in (Order.Status.SHIPPED, Order.Status.DELIVERED):
        raise OrderError("Shipped or delivered orders can't be cancelled.")

    for line in order.items.select_related("product").order_by("product_id"):
        record_stock_movement(
            product=line.product,
            quantity=line.quantity,
            movement_type=StockMovement.MovementType.RETURN,
            performed_by=performed_by,
            reference=f"Order #{order.pk} cancelled",
        )

    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order
