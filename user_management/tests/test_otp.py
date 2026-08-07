import pytest
from django.urls import reverse
from user_management.services import OTPService
from core.models import OTPPurpose


@pytest.mark.django_db
class TestSignupOTPVerification:
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

    def test_signup_verify_otp_locks_out_after_max_attempts(
        self, api_client, make_user, settings
    ):
        user = make_user(email="lockout@email.com")
        OTPService.generate(user.email, OTPPurpose.SIGNUP)

        for _ in range(settings.OTP_MAX_ATTEMPTS):
            api_client.post(
                reverse("signup-otp-verify"), {"email": user.email, "otp": "0000"}
            )

        response = api_client.post(
            reverse("signup-otp-verify"), {"email": user.email, "otp": "0000"}
        )

        assert response.status_code == 400
        assert "too many" in response.data["toast"].lower()

    def test_signup_resend_otp_respects_cooldown(self, api_client, make_user):
        user = make_user(email="cooldown@email.com")

        first_res = api_client.post(reverse("signup-resend-otp"), {"email": user.email})
        second_res = api_client.post(
            reverse("signup-resend-otp"), {"email": user.email}
        )

        assert first_res.status_code == 200
        assert second_res.status_code == 429

    # TODO: test forget password OTP
