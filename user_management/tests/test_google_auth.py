import pytest
from django.urls import reverse
from user_management.models import User

# Target the patch to where verify_oauth2_token is imported/used in your view module
PATCH_TARGET = "user_management.views.auth.google_id_token.verify_oauth2_token"


@pytest.fixture
def google_payload():
    return {
        "iss": "https://accounts.google.com",
        "sub": "1234567890",
        "email": "googleuser@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "https://example.com/avatar.jpg",
    }


@pytest.mark.django_db
class TestGoogleAuth:
    def test_creates_verified_user_from_valid_token(
        self, api_client, mocker, google_payload
    ):
        mocker.patch(PATCH_TARGET, return_value=google_payload)

        response = api_client.post(reverse("google-auth"), {"id_token": "fake-token"})

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["toast"] == "Welcome to DevEdu Google User"

        user = User.objects.get(email="googleuser@example.com")
        assert user.is_verified is True
        assert user.full_name == "Google User"
        assert user.auth_provider == User.AuthProvider.GOOGLE
        assert not user.has_usable_password()

    def test_logs_in_existing_user(self, api_client, mocker, google_payload):
        User.objects.create(
            email="googleuser@example.com",
            full_name="Google User",
            auth_provider=User.AuthProvider.GOOGLE,
        )

        mocker.patch(PATCH_TARGET, return_value=google_payload)

        response = api_client.post(reverse("google-auth"), {"id_token": "fake-token"})

        assert response.status_code == 200
        assert response.data["toast"] == "Welcome back, Google User"
        assert User.objects.filter(email="googleuser@example.com").count() == 1

    def test_invalid_token_rejected(self, api_client, mocker):
        mocker.patch(PATCH_TARGET, side_effect=ValueError("bad token"))

        response = api_client.post(reverse("google-auth"), {"id_token": "bad-token"})

        assert response.status_code == 400
        assert response.data["toast"] == "Invalid Google token"

    def test_unverified_email_rejected(self, api_client, mocker, google_payload):
        google_payload["email_verified"] = False
        mocker.patch(PATCH_TARGET, return_value=google_payload)

        response = api_client.post(reverse("google-auth"), {"id_token": "fake-token"})

        assert response.status_code == 400
        assert response.data["toast"] == "Google account email is not verified."
        assert not User.objects.filter(email="googleuser@example.com").exists()
