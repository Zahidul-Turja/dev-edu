from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from user_management.models import User
from user_management.serializers import SignupSerializer


# Create your views here.
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            if User.objects.filter(email=serializer.validated_data["email"]).exists():
                return Response(
                    {"message": "You already signed up. Please try login"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = serializer.save()

            # TODO: generate and send OTP
        except Exception as e:
            return Response(
                {
                    "message": "Signup failed",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
