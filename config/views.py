from rest_framework.response import Response
from rest_framework import status, permissions, views


class HealthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"message": "K"})
