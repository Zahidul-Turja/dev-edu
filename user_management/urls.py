from django.urls import path

from user_management.views.auth import SignupView, SignupVerifyOTPView

auth_urlpatterns_v1 = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", SignupVerifyOTPView.as_view(), name="signup_otp_verify"),
]
