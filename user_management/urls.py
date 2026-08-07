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
    GoogleAuthView,
)
from user_management.views.users import UserOwnProfileView

auth_urlpatterns_v1 = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", SignupVerifyOTPView.as_view(), name="signup-otp-verify"),
    path(
        "signup/resend-otp/", GeneralResendOTPView.as_view(), name="signup-resend-otp"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "forget-password/request/",
        ForgetPasswordRequestView.as_view(),
        name="forget-password-request",
    ),
    path(
        "forget-password/verify-otp/",
        ForgetPasswordVerifyOTPView.as_view(),
        name="forget-password-verify-otp",
    ),
    path(
        "forget-password/resend-otp/",
        GeneralResendOTPView.as_view(),
        name="forget-password-resend-otp",
    ),
    path(
        "forget-password/confirm/",
        ForgetPasswordConfirmView.as_view(),
        name="forget-password-confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("google/", GoogleAuthView.as_view(), name="google-auth"),
]


user_urlpatterns_v1 = [
    path("", UserOwnProfileView.as_view(), name="view-own-profile"),
]
