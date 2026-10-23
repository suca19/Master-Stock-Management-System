import pytest

from users.models import User
from users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


class TestLogin:
    def test_returns_tokens_and_user(self, api_client):
        user = UserFactory(role=User.MANAGER)
        response = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        )

        assert response.status_code == 200
        assert {"access", "refresh", "user"} <= response.data.keys()
        assert response.data["user"]["role"] == "manager"

    def test_wrong_password(self, api_client):
        user = UserFactory()
        response = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "nope"}, format="json"
        )
        assert response.status_code == 401

    def test_access_token_authenticates_requests(self, api_client):
        user = UserFactory()
        tokens = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        ).data

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        assert api_client.get("/api/users/profile/").data["email"] == user.email

    def test_refresh_token_gives_new_access_token(self, api_client):
        user = UserFactory()
        tokens = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        ).data

        response = api_client.post(
            "/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        assert response.status_code == 200
        assert "access" in response.data
