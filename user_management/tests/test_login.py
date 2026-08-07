import pytest
from django.urls import reverse
from core.models import ToastType


@pytest.mark.django_db
class TestLogin:
    def test_login_fails_if_not_verified(self, api_client, make_user):
        make_user(email="user@email.com", password="strongPass123!", is_verified=False)

        response = api_client.post(
            reverse("login"), {"email": "user@email.com", "password": "strongPass123!"}
        )

        assert response.status_code == 401

    def test_login_invalid_email(self, api_client):
        response = api_client.post(
            reverse("login"), {"email": "randomEmail", "password": "password"}
        )

        data = response.json()

        assert response.status_code == 400
        assert data["toast_type"] == ToastType.ERROR
        assert data["errors"][0]["field"] == "email"

    def test_login_success_returns_tokens(self, api_client, make_user):
        make_user(
            email="email@email.com",
            password="strongPass123!",
            is_verified=True,
        )

        response = api_client.post(
            reverse("login"), {"email": "email@email.com", "password": "strongPass123!"}
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_success_email_case_insensitive(self, api_client, make_user):
        make_user(
            email="EmaIl@email.com",
            password="strongPass123!",
            is_verified=True,
        )

        response = api_client.post(
            reverse("login"), {"email": "email@email.com", "password": "strongPass123!"}
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
