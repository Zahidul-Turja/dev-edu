from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from user_management.serializers import (
    SignupSerializer,
    EmailSerializer,
    EmailOTPSerializer,
    UserOwnProfileSerializer,
    EmailPasswordSerializer,
    ResetPasswordSerializer,
)
from user_management.services import OTPService, ResetTokenService
from user_management.tokens import PasswordResetToken
from core.exceptions import (
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPCooldownError,
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
                    "toast": "Failed to signup",
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

        try:
            code = OTPService.generate(
                email=user.email,
                purpose=OTPPurpose.SIGNUP,
            )
        except (
            OTPExpiredError,
            OTPMaxAttemptsError,
            OTPInvalidError,
            OTPCooldownError,
        ) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: send OTP to email

        return Response(
            {
                "toast": f"Please verify OTP sent to {user.email}.",
            },
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
        except (
            OTPExpiredError,
            OTPMaxAttemptsError,
            OTPInvalidError,
            OTPCooldownError,
        ) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User.objects.filter(email=email).update(is_verified=True)

        user = User.objects.get(email__iexact=email)
        refresh = RefreshToken.for_user(user=user)
        serializer = UserOwnProfileSerializer(user, context={"request": request})

        response_body = serializer.validated_data
        response_body["toast"] = f"Welcome to DevEdu {user.full_name}"
        response_body["access"] = str(refresh.access_token)
        response_body["refresh"] = str(refresh)

        return Response(
            response_body,
            status=status.HTTP_200_OK,
        )


class GeneralResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_request"

    def post(self, request):
        route_name = request.resolver_match.url_name

        serializer = EmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to resend OTP.",
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if route_name == "signup_resend_otp":
            purpose = OTPPurpose.SIGNUP
        else:
            return Response(
                {
                    "toast": "Something went wrong.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            code = OTPService.generate(
                email=serializer.validated_data["email"],
                purpose=purpose,
            )
        except (
            OTPExpiredError,
            OTPMaxAttemptsError,
            OTPInvalidError,
        ) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OTPCooldownError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # TODO: send OTP to email

        return Response(
            {
                "toast": f"OTP resent to {serializer.validated_data["email"]}.",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

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

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

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

        response_body = serializer.validated_data
        response_body["toast"] = f"Welcome back {user.full_name}"
        response_body["access"] = str(refresh.access_token)
        response_body["refresh"] = str(refresh)

        return Response(
            response_body,
            status=status.HTTP_200_OK,
        )


class ForgetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_request"

    def post(self, request):
        serializer = EmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Invalid request",
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            try:
                code = OTPService.generate(email, OTPPurpose.FORGET_PASSWORD)
                # TODO: send otp
                # send_otp_email.delay(email, code, purpose="password_reset")
            except OTPCooldownError:
                pass

        return Response(
            {
                "message": "If this email is registered, a reset OTP has been sent.",
            },
            status=status.HTTP_200_OK,
        )


class ForgetPasswordVerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = EmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip()
        otp = serializer.validated_data["otp"]

        try:
            OTPService.verify(email, otp, OTPPurpose.FORGET_PASSWORD)
        except (
            OTPExpiredError,
            OTPMaxAttemptsError,
            OTPInvalidError,
            OTPCooldownError,
        ) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.get(email__iexact=email)
        token = PasswordResetToken.for_user(user)
        return Response(
            {"reset_token": str(token)},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            token = PasswordResetToken(request.data.get("reset_token"))
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")

        # JSON web token ID (JTI)
        jti = token["jti"]
        if ResetTokenService.reset_token_exists(jti=jti):
            raise AuthenticationFailed("Token already used")

        user_id = token["user_id"]

        ResetTokenService.set_reset_token(jti=jti)

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"  # you're missing this too

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = PasswordResetToken(serializer.validated_data["reset_token"])
        except TokenError:
            raise AuthenticationFailed("Invalid or expired token")

        jti = token["jti"]
        if not ResetTokenService.claim_reset_token(jti):  # see #2 below
            raise AuthenticationFailed("Token already used")

        user = User.objects.get(id=token["user_id"])
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK,
        )
