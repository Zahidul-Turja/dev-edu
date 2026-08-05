from django.urls import path

from user_management.views.auth import SignupView, SignupVerifyOTPView, LoginView
from user_management.views.users import UserOwnProfileView

auth_urlpatterns_v1 = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", SignupVerifyOTPView.as_view(), name="signup_otp_verify"),
    path("login/", LoginView.as_view(), name="login"),
]


user_urlpatterns_v1 = [
    path("", UserOwnProfileView.as_view(), name="view_own_profile"),
]
