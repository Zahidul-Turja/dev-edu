import pytest
from django.urls import reverse
from user_management.models import SocialLink


@pytest.mark.django_db
class TestUserOwnProfile:

    def test_get_profile_authenticated(self, api_client, make_user):
        user = make_user(
            email="test@example.com",
            full_name="Test User",
            is_verified=True,
        )

        # authenticate
        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("view-own-profile"))

        assert response.status_code == 200
        data = response.data

        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "avatar" in data
        assert "social_links" in data

    def test_get_profile_unauthenticated_fails(self, api_client):
        response = api_client.get(reverse("view-own-profile"))

        assert response.status_code == 401

    def test_profile_includes_social_links(self, api_client, make_user):
        user = make_user(email="test2@example.com")

        SocialLink.objects.create(
            user=user, platform="github", url="https://github.com/test"
        )

        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("view-own-profile"))

        assert response.status_code == 200
        assert len(response.data["social_links"]) == 1
        assert response.data["social_links"][0]["platform"] == "github"

    def test_avatar_is_absolute_url(self, api_client, make_user, settings):
        user = make_user(email="avatar@example.com")

        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("view-own-profile"))

        assert response.status_code == 200
        assert response.data["avatar"].startswith("http")
