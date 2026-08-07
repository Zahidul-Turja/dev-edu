from django.urls import path

from user_management.views.auth import (
    SignupView,
    SignupVerifyOTPView,
    LoginView,
    GeneralResendOTPView,
    ForgetPasswordRequestView,
    ForgetPasswordVerifyOTPView,
    ForgetPasswordConfirmView,
    ChangePasswordView,
)
from user_management.views.users import UserOwnProfileView

auth_urlpatterns_v1 = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", SignupVerifyOTPView.as_view(), name="signup_otp_verify"),
    path(
        "signup/resend-otp/", GeneralResendOTPView.as_view(), name="signup_resend_otp"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "forget-password/request/",
        ForgetPasswordRequestView.as_view(),
        name="forget_password_request",
    ),
    path(
        "forget-password/verify-otp/",
        ForgetPasswordVerifyOTPView.as_view(),
        name="forget_password_verify_otp",
    ),
    path(
        "forget-password/resend-otp/",
        GeneralResendOTPView.as_view(),
        name="forget_password_resend_otp",
    ),
    path(
        "forget-password/confirm/",
        ForgetPasswordConfirmView.as_view(),
        name="forget_password_confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]


user_urlpatterns_v1 = [
    path("", UserOwnProfileView.as_view(), name="view_own_profile"),
]
