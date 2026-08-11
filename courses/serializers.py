from rest_framework import serializers
from courses.models import Category


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]
        read_only_fields = ["slug"]
