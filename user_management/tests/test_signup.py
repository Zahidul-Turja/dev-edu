import pytest
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from user_management.models import User


@pytest.mark.django_db
class TestSignup:
    def test_signup_creates_unverified_user_and_send_otp(self, api_client):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "gender": User.Gender.MALE,
            "date_of_birth": "2000-04-24",
        }

        response = api_client.post(reverse("signup"), payload)

        assert response.status_code == 201
        user = User.objects.get(email="new@example.com")
        assert user.is_verified is False
        assert len(mail.outbox) == 1
        assert "verification code" in mail.outbox[0].subject.lower()
