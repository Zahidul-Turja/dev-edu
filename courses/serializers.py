import os
from rest_framework import serializers
from django.urls import reverse
from django.db.models import Max

from courses.models import Category, Course, Section, Lecture
from core.helper_functions import rich_text_to_plain_text
from media_processing.models import VideoAsset
from user_management.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]
        read_only_fields = ["slug"]


class InstructorSummarySerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "avatar"]

    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar_val = obj.get_avatar()
        if request and avatar_val:
            return request.build_absolute_uri(avatar_val)
        return avatar_val


class VideoAssetSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoAsset
        fields = [
            "id",
            "status",
            "duration_seconds",
            "source_height",
            "error_message",
            "created_at",
        ]


# ---------------------------------------------------------------------------
# Public / Student Serializers (Curriculum & Course Details)
# ---------------------------------------------------------------------------

class PublicLectureSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = [
            "id",
            "title",
            "order",
            "content_type",
            "is_preview",
            "duration_seconds",
            "stream_url",
            "pdf_url",
        ]

    def get_duration_seconds(self, obj):
        if obj.video_asset:
            return obj.video_asset.duration_seconds
        return None

    def get_stream_url(self, obj):
        request = self.context.get("request")
        # Only expose stream URL for preview lectures in public view
        if obj.is_preview and obj.content_type == Lecture.ContentType.VIDEO and obj.video_asset:
            path = reverse(
                "course-lecture-stream",
                kwargs={"course_slug": obj.section.course.slug, "lecture_id": obj.id},
            )
            return request.build_absolute_uri(path) if request else path
        return None

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.is_preview and obj.content_type == Lecture.ContentType.PDF and obj.pdf_file:
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return None


class PublicSectionSerializer(serializers.ModelSerializer):
    lectures = PublicLectureSerializer(many=True, read_only=True)
    total_lectures = serializers.SerializerMethodField()
    total_duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "title", "order", "total_lectures", "total_duration_seconds", "lectures"]

    def get_total_lectures(self, obj):
        return obj.lectures.count()

    def get_total_duration_seconds(self, obj):
        total = 0
        for lec in obj.lectures.all():
            if lec.video_asset and lec.video_asset.duration_seconds:
                total += lec.video_asset.duration_seconds
        return total


class PublicCourseListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    instructor = InstructorSummarySerializer(read_only=True)
    total_sections = serializers.SerializerMethodField()
    total_lectures = serializers.SerializerMethodField()
    total_duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "thumbnail",
            "price",
            "level",
            "language",
            "category",
            "instructor",
            "total_sections",
            "total_lectures",
            "total_duration_seconds",
            "created_at",
        ]

    def get_total_sections(self, obj):
        return obj.sections.count()

    def get_total_lectures(self, obj):
        return Lecture.objects.filter(section__course=obj).count()

    def get_total_duration_seconds(self, obj):
        total = 0
        lectures = Lecture.objects.filter(section__course=obj).select_related("video_asset")
        for lec in lectures:
            if lec.video_asset and lec.video_asset.duration_seconds:
                total += lec.video_asset.duration_seconds
        return total


class PublicCourseDetailSerializer(PublicCourseListSerializer):
    sections = PublicSectionSerializer(many=True, read_only=True)

    class Meta(PublicCourseListSerializer.Meta):
        fields = PublicCourseListSerializer.Meta.fields + [
            "description",
            "description_rich",
            "requirements",
            "what_you_will_learn",
            "sections",
        ]


# ---------------------------------------------------------------------------
# Instructor Serializers (Full CRUD, Ordering & Management)
# ---------------------------------------------------------------------------

class InstructorLectureSerializer(serializers.ModelSerializer):
    video_asset = VideoAssetSummarySerializer(read_only=True)

    class Meta:
        model = Lecture
        fields = [
            "id",
            "section",
            "title",
            "order",
            "content_type",
            "is_preview",
            "video_asset",
            "pdf_file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "section", "video_asset", "created_at", "updated_at"]


class InstructorLectureCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False, min_value=1)

    class Meta:
        model = Lecture
        fields = [
            "id",
            "title",
            "order",
            "content_type",
            "is_preview",
            "pdf_file",
        ]

    def create(self, validated_data):
        section = self.context["section"]
        if "order" not in validated_data:
            highest_order = section.lectures.aggregate(Max("order"))["order__max"] or 0
            validated_data["order"] = highest_order + 1
        validated_data["section"] = section
        return super().create(validated_data)


class InstructorSectionSerializer(serializers.ModelSerializer):
    lectures = InstructorLectureSerializer(many=True, read_only=True)
    total_lectures = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            "id",
            "course",
            "title",
            "order",
            "total_lectures",
            "lectures",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "course", "created_at", "updated_at"]

    def get_total_lectures(self, obj):
        return obj.lectures.count()


class InstructorSectionCreateUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False, min_value=1)

    class Meta:
        model = Section
        fields = ["id", "title", "order"]

    def create(self, validated_data):
        course = self.context["course"]
        if "order" not in validated_data:
            highest_order = course.sections.aggregate(Max("order"))["order__max"] or 0
            validated_data["order"] = highest_order + 1
        validated_data["course"] = course
        return super().create(validated_data)


class ReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)


class ReorderListSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True)


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "subtitle",
            "description_rich",
            "requirements",
            "what_you_will_learn",
            "category",
            "level",
            "language",
            "thumbnail",
            "price",
            "status",
        ]

    def create(self, validated_data):
        validated_data["instructor"] = self.context["request"].user
        desc_rich = validated_data.get("description_rich", "")
        validated_data["description"] = rich_text_to_plain_text(desc_rich)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "description_rich" in validated_data:
            desc_rich = validated_data.get("description_rich", "")
            validated_data["description"] = rich_text_to_plain_text(desc_rich)
        return super().update(instance, validated_data)


class InstructorCourseDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    sections = InstructorSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "description",
            "description_rich",
            "requirements",
            "what_you_will_learn",
            "category",
            "level",
            "language",
            "thumbnail",
            "price",
            "status",
            "is_verified",
            "sections",
            "created_at",
            "updated_at",
        ]


class VideoUploadSerializer(serializers.Serializer):
    ALLOWED_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]
    MAX_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

    video_file = serializers.FileField()

    def validate_video_file(self, file_obj):
        _, ext = os.path.splitext(file_obj.name)
        if ext.lower() not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported video format: {ext}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        if file_obj.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError("Video file size cannot exceed 2GB.")
        return file_obj
