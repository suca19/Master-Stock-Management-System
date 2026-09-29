from decimal import Decimal

import factory

from inventory.models import Category, Product, Supplier


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    sku = factory.Sequence(lambda n: f'SKU-{n:04d}')
    name = factory.Sequence(lambda n: f'Product {n}')
    category = factory.SubFactory(CategoryFactory)
    cost_price = Decimal('4.00')
    price = Decimal('10.00')
    stock = 0


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    name = factory.Sequence(lambda n: f'Supplier {n}')
