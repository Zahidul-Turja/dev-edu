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
)
from user_management.services import OTPService
from core.exceptions import (
    OTPCooldownError,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
)
from core.models import OTPPurpose

User = get_user_model()


# Create your views here.
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            if User.objects.filter(
                email__iexact=serializer.validated_data["email"]
            ).exists():
                return Response(
                    {"message": "You already signed up. Please try login"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = serializer.save()

            code = OTPService.generate(
                email=user.email,
                purpose=OTPPurpose.SIGNUP,
            )
            # TODO: send OTP to email

        except Exception as e:
            return Response(
                {
                    "error_message": "Signup failed. Please try again later.",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SignupVerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = EmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
        response_body["message"] = "Account verified successfully."
        response_body["access"] = str(refresh.access_token)
        response_body["refresh"] = str(refresh)

        return Response(
            response_body,
            status=status.HTTP_200_OK,
        )
