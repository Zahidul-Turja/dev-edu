import pytest
from django.urls import reverse
from core.models import OTPPurpose


@pytest.mark.django_db
class TestForgetPassword:

    def test_forget_password_flow_success(self, api_client, make_user, fake_redis):
        user = make_user(
            email="email@email.com", password="OldPassword123", is_verified=True
        )

        # Set OTP
        api_client.post(
            reverse("forget-password-request"), {"email": "email@email.com"}
        )
        cache_key = f"otp:{user.email}:code:{OTPPurpose.FORGET_PASSWORD}"
        code = fake_redis.get(cache_key).decode()

        otp_verification_response = api_client.post(
            reverse("forget-password-verify-otp"),
            {
                "email": "email@email.com",
                "otp": code,
            },
        )

        # Verify OTP
        otp_verification_data = otp_verification_response.json()

        assert otp_verification_response.status_code == 200
        assert "reset_token" in otp_verification_data

        # Set new password
        password_reset_response = api_client.post(
            reverse("forget-password-confirm"),
            {
                "reset_token": otp_verification_data["reset_token"],
                "new_password": "newStrongPass123",
            },
        )

        assert password_reset_response.status_code == 200

        # Login with new password
        login_response = api_client.post(
            reverse("login"),
            {"email": "email@email.com", "password": "newStrongPass123"},
        )
        assert login_response.status_code == 200

    def test_forget_password_wrong_otp(self, api_client, make_user, fake_redis):
        make_user(email="email@email.com", password="OldPassword123", is_verified=True)

        # Set OTP
        api_client.post(
            reverse("forget-password-request"), {"email": "email@email.com"}
        )

        response = api_client.post(
            reverse("forget-password-verify-otp"),
            {
                "email": "email@email.com",
                "otp": "0000",
            },
        )

        assert response.status_code == 400
