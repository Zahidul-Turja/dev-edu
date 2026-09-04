from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.helper_functions import format_serializer_errors
from core.models import ToastType
from courses.models import Category, Course, Lecture, Section
from courses.permissions import IsCourseOwner, IsInstructorRole
from courses.serializers import (
    CategorySerializer,
    CourseCreateSerializer,
    InstructorCourseDetailSerializer,
    InstructorLectureCreateUpdateSerializer,
    InstructorLectureSerializer,
    InstructorSectionCreateUpdateSerializer,
    InstructorSectionSerializer,
    PublicCourseDetailSerializer,
    PublicCourseListSerializer,
    ReorderListSerializer,
    VideoAssetSummarySerializer,
    VideoUploadSerializer,
)
from media_processing.models import VideoAsset
from media_processing.services import get_ranged_file_response
from media_processing.tasks import process_video_asset


class GenericPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ---------------------------------------------------------------------------
# Public / Student Views
# ---------------------------------------------------------------------------

class CategoryListView(ListAPIView):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = GenericPagination


class PublicCourseListView(ListAPIView):
    serializer_class = PublicCourseListSerializer
    permission_classes = [AllowAny]
    pagination_class = GenericPagination

    def get_queryset(self):
        queryset = (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "instructor")
            .prefetch_related("sections__lectures")
        )

        category_param = self.request.query_params.get("category")
        if category_param:
            if category_param.isdigit():
                queryset = queryset.filter(category_id=category_param)
            else:
                queryset = queryset.filter(category__slug=category_param)

        level = self.request.query_params.get("level")
        if level:
            queryset = queryset.filter(level=level)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(subtitle__icontains=search) | Q(description__icontains=search)
            )

        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering in ("price", "-price", "created_at", "-created_at", "title", "-title"):
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-created_at")

        return queryset


class PublicCourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        course = get_object_or_404(
            Course.objects.select_related("category", "instructor").prefetch_related(
                "sections__lectures__video_asset"
            ),
            slug=slug,
        )

        # Non-owners can only view published courses
        if course.status != Course.Status.PUBLISHED:
            if not (request.user.is_authenticated and (request.user.is_staff or course.instructor_id == request.user.id)):
                return Response(
                    {"detail": "Course not found or not published."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = PublicCourseDetailSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LectureStreamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_slug, lecture_id):
        lecture = get_object_or_404(
            Lecture.objects.select_related("section__course", "video_asset"),
            id=lecture_id,
            section__course__slug=course_slug,
        )

        # Access check: is_preview allows anyone to stream.
        # Otherwise, only course owner / staff / enrolled students can stream.
        if not lecture.is_preview:
            is_authorized = (
                request.user.is_authenticated
                and (request.user.is_staff or lecture.section.course.instructor_id == request.user.id)
            )
            if not is_authorized:
                return Response(
                    {"detail": "You do not have permission to view this content. Enrollment required."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if lecture.content_type != Lecture.ContentType.VIDEO or not lecture.video_asset:
            return Response(
                {"detail": "This lecture does not contain a video asset."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        asset = lecture.video_asset
        if asset.status == VideoAsset.Status.FAILED:
            return Response(
                {"detail": f"Video processing failed: {asset.error_message}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if asset.status != VideoAsset.Status.READY:
            return Response(
                {"detail": "Video is currently processing. Please try again shortly."},
                status=status.HTTP_409_CONFLICT,
            )

        range_header = request.headers.get("Range") or request.META.get("HTTP_RANGE")
        return get_ranged_file_response(asset.original_file.path, range_header=range_header)


# ---------------------------------------------------------------------------
# Instructor Views (Course CRUD)
# ---------------------------------------------------------------------------

class InstructorCourseListCreateView(APIView):
    permission_classes = [IsInstructorRole]

    def get(self, request):
        courses = Course.objects.filter(instructor=request.user).order_by("-created_at")
        paginator = GenericPagination()
        page = paginator.paginate_queryset(courses, request)
        serializer = InstructorCourseDetailSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data, context={"request": request})
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
                "id": course.id,
                "slug": course.slug,
                "toast": "Course created successfully",
                "toast_type": ToastType.SUCCESS,
            },
            status=status.HTTP_201_CREATED,
        )


class InstructorCourseDetailView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def get_object(self, request, slug):
        course = get_object_or_404(
            Course.objects.select_related("category").prefetch_related(
                "sections__lectures__video_asset"
            ),
            slug=slug,
        )
        self.check_object_permissions(request, course)
        return course

    def get(self, request, slug):
        course = self.get_object(request, slug)
        serializer = InstructorCourseDetailSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, slug):
        return self._update(request, slug, partial=False)

    def patch(self, request, slug):
        return self._update(request, slug, partial=True)

    def _update(self, request, slug, partial):
        course = self.get_object(request, slug)
        serializer = CourseCreateSerializer(
            course, data=request.data, partial=partial, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to update course",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated_course = serializer.save()
        return Response(
            {
                "slug": updated_course.slug,
                "toast": "Course updated successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorCourseDetailSerializer(updated_course, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, slug):
        course = self.get_object(request, slug)
        course.delete()
        return Response(
            {
                "toast": "Course deleted successfully",
                "toast_type": ToastType.SUCCESS,
            },
            status=status.HTTP_200_OK,
        )


# Compatibility alias
CourseCreateUpdateView = InstructorCourseListCreateView


# ---------------------------------------------------------------------------
# Instructor Views (Section CRUD & Reorder)
# ---------------------------------------------------------------------------

class InstructorSectionListCreateView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def get_course(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        self.check_object_permissions(request, course)
        return course

    def get(self, request, course_slug):
        course = self.get_course(request, course_slug)
        sections = course.sections.prefetch_related("lectures__video_asset").order_by("order")
        serializer = InstructorSectionSerializer(sections, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, course_slug):
        course = self.get_course(request, course_slug)
        serializer = InstructorSectionCreateUpdateSerializer(
            data=request.data, context={"course": course, "request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to create section",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        section = serializer.save()
        return Response(
            {
                "toast": "Section created successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorSectionSerializer(section, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class InstructorSectionDetailView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def get_object(self, request, course_slug, pk):
        section = get_object_or_404(
            Section.objects.select_related("course").prefetch_related("lectures__video_asset"),
            id=pk,
            course__slug=course_slug,
        )
        self.check_object_permissions(request, section)
        return section

    def get(self, request, course_slug, pk):
        section = self.get_object(request, course_slug, pk)
        serializer = InstructorSectionSerializer(section, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, course_slug, pk):
        return self._update(request, course_slug, pk, partial=False)

    def patch(self, request, course_slug, pk):
        return self._update(request, course_slug, pk, partial=True)

    def _update(self, request, course_slug, pk, partial):
        section = self.get_object(request, course_slug, pk)
        serializer = InstructorSectionCreateUpdateSerializer(
            section, data=request.data, partial=partial, context={"course": section.course, "request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to update section",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated_section = serializer.save()
        return Response(
            {
                "toast": "Section updated successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorSectionSerializer(updated_section, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, course_slug, pk):
        section = self.get_object(request, course_slug, pk)
        section.delete()
        return Response(
            {
                "toast": "Section deleted successfully",
                "toast_type": ToastType.SUCCESS,
            },
            status=status.HTTP_200_OK,
        )


class InstructorSectionReorderView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        self.check_object_permissions(request, course)

        serializer = ReorderListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Invalid reorder data",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = serializer.validated_data["items"]
        item_ids = [item["id"] for item in items]
        sections = {sec.id: sec for sec in course.sections.filter(id__in=item_ids)}

        if len(sections) != len(item_ids):
            return Response(
                {"toast": "One or more section IDs are invalid for this course", "toast_type": ToastType.ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Step 1: Temporarily negate orders to avoid unique_together collision
            for idx, item in enumerate(items, start=1):
                Section.objects.filter(id=item["id"]).update(order=10000 + idx)
            # Step 2: Set target orders
            for item in items:
                Section.objects.filter(id=item["id"]).update(order=item["order"])

        updated_sections = course.sections.order_by("order")
        return Response(
            {
                "toast": "Sections reordered successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorSectionSerializer(updated_sections, many=True, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Instructor Views (Lecture CRUD, Reorder & Video Upload)
# ---------------------------------------------------------------------------

class InstructorLectureListCreateView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def get_section(self, request, course_slug, section_id):
        section = get_object_or_404(
            Section.objects.select_related("course"),
            id=section_id,
            course__slug=course_slug,
        )
        self.check_object_permissions(request, section)
        return section

    def get(self, request, course_slug, section_id):
        section = self.get_section(request, course_slug, section_id)
        lectures = section.lectures.select_related("video_asset").order_by("order")
        serializer = InstructorLectureSerializer(lectures, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, course_slug, section_id):
        section = self.get_section(request, course_slug, section_id)
        serializer = InstructorLectureCreateUpdateSerializer(
            data=request.data, context={"section": section, "request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to create lecture",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        lecture = serializer.save()
        return Response(
            {
                "toast": "Lecture created successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorLectureSerializer(lecture, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class InstructorLectureDetailView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def get_object(self, request, course_slug, pk):
        lecture = get_object_or_404(
            Lecture.objects.select_related("section__course", "video_asset"),
            id=pk,
            section__course__slug=course_slug,
        )
        self.check_object_permissions(request, lecture)
        return lecture

    def get(self, request, course_slug, pk):
        lecture = self.get_object(request, course_slug, pk)
        serializer = InstructorLectureSerializer(lecture, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, course_slug, pk):
        return self._update(request, course_slug, pk, partial=False)

    def patch(self, request, course_slug, pk):
        return self._update(request, course_slug, pk, partial=True)

    def _update(self, request, course_slug, pk, partial):
        lecture = self.get_object(request, course_slug, pk)
        serializer = InstructorLectureCreateUpdateSerializer(
            lecture, data=request.data, partial=partial, context={"section": lecture.section, "request": request}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Failed to update lecture",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated_lecture = serializer.save()
        return Response(
            {
                "toast": "Lecture updated successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorLectureSerializer(updated_lecture, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, course_slug, pk):
        lecture = self.get_object(request, course_slug, pk)
        lecture.delete()
        return Response(
            {
                "toast": "Lecture deleted successfully",
                "toast_type": ToastType.SUCCESS,
            },
            status=status.HTTP_200_OK,
        )


class InstructorLectureReorderView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def post(self, request, course_slug, section_id):
        section = get_object_or_404(
            Section.objects.select_related("course"),
            id=section_id,
            course__slug=course_slug,
        )
        self.check_object_permissions(request, section)

        serializer = ReorderListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Invalid reorder data",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = serializer.validated_data["items"]
        item_ids = [item["id"] for item in items]
        lectures = {lec.id: lec for lec in section.lectures.filter(id__in=item_ids)}

        if len(lectures) != len(item_ids):
            return Response(
                {"toast": "One or more lecture IDs are invalid for this section", "toast_type": ToastType.ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for idx, item in enumerate(items, start=1):
                Lecture.objects.filter(id=item["id"]).update(order=10000 + idx)
            for item in items:
                Lecture.objects.filter(id=item["id"]).update(order=item["order"])

        updated_lectures = section.lectures.select_related("video_asset").order_by("order")
        return Response(
            {
                "toast": "Lectures reordered successfully",
                "toast_type": ToastType.SUCCESS,
                "data": InstructorLectureSerializer(updated_lectures, many=True, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class InstructorLectureVideoUploadView(APIView):
    permission_classes = [IsInstructorRole, IsCourseOwner]

    def post(self, request, course_slug, pk):
        lecture = get_object_or_404(
            Lecture.objects.select_related("section__course", "video_asset"),
            id=pk,
            section__course__slug=course_slug,
        )
        self.check_object_permissions(request, lecture)

        if lecture.content_type != Lecture.ContentType.VIDEO:
            return Response(
                {"toast": "This lecture is not configured for video content.", "toast_type": ToastType.ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VideoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "toast": "Video upload failed",
                    "toast_type": ToastType.ERROR,
                    "errors": format_serializer_errors(serializer.errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        video_file = serializer.validated_data["video_file"]

        # Create or replace VideoAsset
        old_asset = lecture.video_asset
        asset = VideoAsset.objects.create(
            original_file=video_file,
            status=VideoAsset.Status.PENDING,
        )
        lecture.video_asset = asset
        lecture.save(update_fields=["video_asset"])

        # Dispatch async task to process media
        process_video_asset.delay(asset.id)

        # Clean up old asset file if existing
        if old_asset:
            old_asset.delete()

        return Response(
            {
                "toast": "Video uploaded successfully and is being processed.",
                "toast_type": ToastType.SUCCESS,
                "data": VideoAssetSummarySerializer(asset).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
