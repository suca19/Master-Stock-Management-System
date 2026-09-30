import pytest

from users.models import User
from users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def registration(**overrides):
    data = {'username': 'newbie', 'email': 'newbie@example.com', 'password': 'Str0ng!Passphrase',
            'password2': 'Str0ng!Passphrase', 'first_name': 'New', 'last_name': 'Person'}
    data.update(overrides)
    return data


class TestLogin:
    def test_returns_tokens_and_user(self, api_client):
        user = UserFactory(role=User.MANAGER)
        response = api_client.post('/api/auth/login/', {'email': user.email, 'password': DEFAULT_PASSWORD},
                                   format='json')

        assert response.status_code == 200
        assert {'access', 'refresh', 'user'} <= response.data.keys()
        assert response.data['user']['role'] == 'manager'

    def test_wrong_password(self, api_client):
        user = UserFactory()
        response = api_client.post('/api/auth/login/', {'email': user.email, 'password': 'nope'}, format='json')
        assert response.status_code == 401

    def test_access_token_authenticates_requests(self, api_client):
        user = UserFactory()
        tokens = api_client.post('/api/auth/login/', {'email': user.email, 'password': DEFAULT_PASSWORD},
                                 format='json').data

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        assert api_client.get('/api/users/profile/').data['email'] == user.email

    def test_refresh_token_gives_new_access_token(self, api_client):
        user = UserFactory()
        tokens = api_client.post('/api/auth/login/', {'email': user.email, 'password': DEFAULT_PASSWORD},
                                 format='json').data

        response = api_client.post('/api/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        assert response.status_code == 200
        assert 'access' in response.data


class TestRegister:
    def test_creates_staff_account(self, api_client):
        response = api_client.post('/api/auth/register/', registration(), format='json')

        assert response.status_code == 201
        assert User.objects.get(email='newbie@example.com').role == User.STAFF

    @pytest.mark.parametrize('role', ['admin', 'manager'])
    def test_cannot_register_with_elevated_role(self, api_client, role):
        response = api_client.post('/api/auth/register/', registration(role=role), format='json')

        assert response.status_code == 201
        assert User.objects.get(email='newbie@example.com').role == User.STAFF

    @pytest.mark.parametrize('password', [
        '1',              # too short
        'password123',    # too common
        '12345678901',    # entirely numeric
        'newbie12',       # too similar to the username
    ])
    def test_rejects_weak_passwords(self, api_client, password):
        response = api_client.post('/api/auth/register/', registration(password=password, password2=password),
                                   format='json')

        assert response.status_code == 400
        assert 'password' in response.data
        assert not User.objects.filter(email='newbie@example.com').exists()

    def test_rejects_mismatched_passwords(self, api_client):
        response = api_client.post('/api/auth/register/', registration(password2='Different!Pass1'), format='json')
        assert response.status_code == 400

    def test_rejects_duplicate_email(self, api_client):
        UserFactory(email='newbie@example.com')
        response = api_client.post('/api/auth/register/', registration(), format='json')
        assert response.status_code == 400

    @pytest.mark.parametrize('field', ['email', 'username', 'first_name', 'last_name'])
    def test_requires_field(self, api_client, field):
        data = registration()
        del data[field]
        assert api_client.post('/api/auth/register/', data, format='json').status_code == 400
