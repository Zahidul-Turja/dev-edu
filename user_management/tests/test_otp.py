import pytest
from django.urls import reverse
from user_management.services import OTPService
from core.models import OTPPurpose


@pytest.mark.django_db
class TestOTPVerification:
    def test_signup_verify_otp_success_activates_user(self, api_client, make_user):
        user = make_user(email="test@email.com")
        code = OTPService.generate(user.email, OTPPurpose.SIGNUP)

        response = api_client.post(
            reverse("signup-otp-verify"), {"email": user.email, "otp": code}
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_verified is True

    def test_signup_verify_otp_wrong_code_fails(self, api_client, make_user):
        user = make_user(email="test@email.com")
        OTPService.generate(user.email, OTPPurpose.SIGNUP)

        response = api_client.post(
            reverse("signup-otp-verify"), {"email": user.email, "otp": "0000"}
        )

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.is_verified is False
