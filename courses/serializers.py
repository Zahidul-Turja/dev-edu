from rest_framework import serializers

from courses.models import Category, Course
from core.helper_functions import rich_text_to_plain_text


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]
        read_only_fields = ["slug"]


class CourseCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = [
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
        validated_data["description"] = rich_text_to_plain_text(
            validated_data["description_rich"]
        )
        return super().create(validated_data)
