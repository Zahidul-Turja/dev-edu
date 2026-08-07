import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestChangePassword:

    def test_unauthenticated_fails(self, api_client):
        response = api_client.post(
            reverse("change-password"),
            {
                "password": "strongPassword123",
                "new_password": "strongPassword123",
            },
        )

        assert response.status_code == 401

    def test_new_same_as_old_password(self, api_client, make_user):
        user = make_user(
            email="email@email.com", password="strongPassword123", is_verified=True
        )

        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("change-password"),
            {
                "password": "strongPassword123",
                "new_password": "strongPassword123",
            },
        )

        assert response.status_code == 400
        assert response.data["errors"][0]["field"] == "new_password"

    def test_incorrect_old_password(self, api_client, make_user):
        user = make_user(
            email="email@email.com",
            password="strongPassword123",
            is_verified=True,
        )

        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("change-password"),
            {
                "password": "IncorrectPassword123",
                "new_password": "NewStrongPass123",
            },
        )

        assert response.status_code == 400

    def test_correct_old_password(self, api_client, make_user):
        user = make_user(
            email="email@email.com",
            password="strongPassword123",
            is_verified=True,
        )

        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("change-password"),
            {
                "password": "strongPassword123",
                "new_password": "NewStrongPass123",
            },
        )

        assert response.status_code == 200

        # Try logging in with old password
        login_response_old = api_client.post(
            reverse("login"),
            {
                "email": "email@email.com",
                "password": "strongPassword123",
            },
        )

        assert login_response_old.status_code == 400

        # Try logging in with new password
        login_response_new = api_client.post(
            reverse("login"),
            {
                "email": "email@email.com",
                "password": "NewStrongPass123",
            },
        )

        assert login_response_new.status_code == 200
