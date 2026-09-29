from django.db import transaction

from .models import Product, StockMovement


class InsufficientStock(Exception):
    def __init__(self, product, requested):
        self.product = product
        self.requested = requested
        super().__init__(
            f"Not enough stock for {product.name}: {product.stock} available, {requested} requested."
        )


@transaction.atomic
def record_stock_movement(*, product, quantity, movement_type, performed_by=None,
                          reference="", notes=""):
    """
    Apply a signed stock delta to a product and record it in the ledger.

    The product row is locked for the rest of the transaction, so concurrent
    movements on the same product are applied one after another.
    """
    locked = Product.objects.select_for_update().get(pk=product.pk)

    new_stock = locked.stock + quantity
    if new_stock < 0:
        raise InsufficientStock(locked, -quantity)

    locked.stock = new_stock
    locked.save(update_fields=["stock", "updated_at"])
    product.stock = new_stock  # keep the caller's instance in sync

    return StockMovement.objects.create(
        product=locked,
        quantity=quantity,
        movement_type=movement_type,
        performed_by=performed_by,
        reference=reference,
        notes=notes,
    )
