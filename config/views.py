from rest_framework.response import Response
from rest_framework import status, permissions, views
from config.tasks import debug_task


class HealthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        debug_task.delay()
        return Response({"message": "K"})
