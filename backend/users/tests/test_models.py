import pytest

from users.models import User

pytestmark = pytest.mark.django_db


def test_create_user_hashes_password_and_defaults_to_staff():
    user = User.objects.create_user(email='Jane@Example.COM', username='jane', password='Secret!123')

    assert user.role == User.STAFF
    assert user.email == 'Jane@example.com'  # domain part is normalised
    assert user.password != 'Secret!123'
    assert user.password.startswith('md5$')  # the fast test hasher; production uses PBKDF2
    assert user.check_password('Secret!123')
    assert not user.is_staff and not user.is_superuser


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email='', username='nobody', password='x')


def test_create_superuser_is_admin():
    user = User.objects.create_superuser(email='root@example.com', username='root', password='Secret!123')
    assert user.role == User.ADMIN
    assert user.is_staff and user.is_superuser


def test_email_is_the_login_field():
    assert User.USERNAME_FIELD == 'email'


def test_full_name_and_str():
    user = User(email='a@example.com', first_name='Ada', last_name='Lovelace', role=User.MANAGER)
    assert user.full_name == 'Ada Lovelace'
    assert str(user) == 'a@example.com (Manager)'
