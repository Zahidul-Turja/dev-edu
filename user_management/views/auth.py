from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from user_management.serializers import (
    SignupSerializer,
    EmailOTPSerializer,
    UserOwnProfileSerializer,
    EmailPasswordSerializer,
)
from user_management.services import OTPService
from core.exceptions import (
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
)
from core.models import OTPPurpose
from core.helper_functions import format_serializer_errors

User = get_user_model()


# Create your views here.
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Signup failed",
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.is_valid(raise_exception=True)

        if User.objects.filter(
            email__iexact=serializer.validated_data["email"]
        ).exists():
            return Response(
                {
                    "toast": "You already signed up. Please try login",
                    "errors": [
                        {
                            "field": "email",
                            "message": "Email already exists",
                        }
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()

        code = OTPService.generate(
            email=user.email,
            purpose=OTPPurpose.SIGNUP,
        )
        # TODO: send OTP to email

        return Response(
            {"toast": f"Please verify OTP sent to {user.email}."},
            status=status.HTTP_201_CREATED,
        )


class SignupVerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = EmailOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "OTP verification failed",
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            OTPService.verify(email, otp, OTPPurpose.SIGNUP)
        except (OTPExpiredError, OTPMaxAttemptsError, OTPInvalidError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User.objects.filter(email=email).update(is_verified=True)

        user = User.objects.get(email__iexact=email)
        refresh = RefreshToken.for_user(user=user)
        serializer = UserOwnProfileSerializer(user, context={"request": request})

        response_body = serializer.data
        response_body["toast"] = f"Welcome to DevEdu {user.full_name}"
        response_body["access"] = str(refresh.access_token)
        response_body["refresh"] = str(refresh)

        return Response(
            response_body,
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Login failed",
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.data["email"]
        password = serializer.data["password"]

        user = User.objects.filter(email__iexact=email).first()
        if not (user and user.check_password(password)):
            return Response(
                {
                    "toast": "Invalid email or password",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user=user)
        serializer = UserOwnProfileSerializer(user, context={"request": request})

        response_body = serializer.data
        response_body["toast"] = f"Welcome back {user.full_name}"
        response_body["access"] = str(refresh.access_token)
        response_body["refresh"] = str(refresh)

        return Response(
            response_body,
            status=status.HTTP_200_OK,
        )
