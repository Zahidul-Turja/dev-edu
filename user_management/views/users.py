from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from user_management.serializers import UserOwnProfileSerializer


class UserOwnProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserOwnProfileSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
