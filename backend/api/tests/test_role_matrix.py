"""
The role permission matrix, tested through the real API.

This file is the spec for who may do what. The rules (decided 2026-10-19: only shop staff log in):

                                 admin   manager   staff          customer / anonymous
  categories, products,          all     all       read           no
  suppliers
  stock movements                all     all       read + create  no
  orders                         all     all       all            no
  users (list/create/delete)     all     read      own only       no
  self-registration              removed: the admin creates accounts

Tests go through HTTP on purpose, so they don't care how the permission classes are written.
"""

import pytest
from rest_framework.test import APIClient

from inventory.tests.factories import CategoryFactory
from users.models import User
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

CATALOG = ["/api/categories/", "/api/products/", "/api/suppliers/"]


@pytest.fixture
def customer_client(db):
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=User.CUSTOMER))
    return client


def client_for(request, role):
    """Turn a role name from a parametrize list into the matching client fixture."""
    return request.getfixturevalue(f"{role}_client" if role else "api_client")


def new_category():
    return {"name": "New category"}


def new_product():
    return {
        "sku": "MATRIX-1",
        "name": "Matrix product",
        "category": CategoryFactory().id,
        "price": "10.00",
        "cost_price": "4.00",
    }


# --- Catalog: categories, products, suppliers ------------------------------------------


@pytest.mark.parametrize("url", CATALOG)
@pytest.mark.parametrize(
    "role, expected",
    [("admin", 200), ("manager", 200), ("staff", 200), ("customer", 403), (None, 401)],
)
def test_catalog_read(request, url, role, expected):
    assert client_for(request, role).get(url).status_code == expected


@pytest.mark.parametrize(
    "url, payload",
    [("/api/categories/", new_category), ("/api/products/", new_product)],
)
@pytest.mark.parametrize(
    "role, expected",
    [("admin", 201), ("manager", 201), ("staff", 403), ("customer", 403), (None, 401)],
)
def test_catalog_write(request, url, payload, role, expected):
    response = client_for(request, role).post(url, payload(), format="json")
    assert response.status_code == expected


# --- Stock movements and orders ----------------------------------------------------------


@pytest.mark.parametrize(
    "role, expected",
    [("admin", 201), ("manager", 201), ("staff", 201), ("customer", 403), (None, 401)],
)
def test_record_stock_movement(request, stocked_product, role, expected):
    response = client_for(request, role).post(
        "/api/stock-movements/",
        {"product": stocked_product.id, "quantity": 1, "movement_type": "in"},
        format="json",
    )
    assert response.status_code == expected


@pytest.mark.parametrize(
    "role, expected",
    [("admin", 200), ("manager", 200), ("staff", 200), ("customer", 403), (None, 401)],
)
def test_list_orders(request, role, expected):
    assert client_for(request, role).get("/api/orders/").status_code == expected


# --- Users -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "role, expected",
    [("admin", 200), ("manager", 200), ("staff", 403), ("customer", 403), (None, 401)],
)
def test_list_users(request, role, expected):
    assert client_for(request, role).get("/api/users/").status_code == expected


def test_staff_cannot_see_another_user(staff_client):
    # 404, not 403: a 403 would confirm that the user id exists
    other = UserFactory()
    assert staff_client.get(f"/api/users/{other.id}/").status_code == 404


def test_staff_can_see_themselves(staff_client, staff_user):
    assert staff_client.get(f"/api/users/{staff_user.id}/").status_code == 200


def test_manager_cannot_create_or_delete_users(manager_client, staff_user):
    created = manager_client.post("/api/users/", {"email": "x@example.com"}, format="json")
    assert created.status_code == 403
    assert manager_client.delete(f"/api/users/{staff_user.id}/").status_code == 403


# --- Registration ------------------------------------------------------------------------


def test_self_registration_is_gone(api_client):
    response = api_client.post(
        "/api/auth/register/", {"email": "intruder@example.com"}, format="json"
    )
    assert response.status_code == 404
