from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from core.models import ToastType
from core.helper_functions import format_serializer_errors
from courses.permissions import IsCourseOwner, IsInstructorRole
from courses.models import Category
from courses.serializers import CategorySerializer, CourseCreateSerializer


# Create your views here.
class GenericPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 16


class CategoryListView(ListAPIView):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = GenericPagination


class CourseCreateUpdateView(APIView):
    permission_classes = [IsInstructorRole]

    def post(self, request):
        serializer = CourseCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to create course",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        course = serializer.save()
        return Response(
            {
                "slug": course.slug,
                "toast": "Course created successfully",
                "toast_type": ToastType.SUCCESS,
            },
            status=status.HTTP_201_CREATED,
        )
