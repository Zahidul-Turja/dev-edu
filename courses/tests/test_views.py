import pytest
from django.urls import reverse
from rest_framework import status
from core.models import ToastType
from courses.models import Category, Course
from courses.serializers import CategorySerializer, CourseCreateSerializer
from user_management.models import User


@pytest.mark.django_db
class TestCategoryListView:
    def test_category_list_success(self, api_client):
        # Create some categories for testing
        Category.objects.create(name="Category 1", icon="icon1.png")
        Category.objects.create(name="Category 2", icon="icon2.png")

        response = api_client.get(reverse("category-list"))

        assert response.status_code == status.HTTP_200_OK
        categories = response.data.get("results", [])
        assert len(categories) == 2

    def test_category_list_empty(self, api_client):
        response = api_client.get(reverse("category-list"))

        assert response.status_code == status.HTTP_200_OK
        categories = response.data.get("results", [])
        assert len(categories) == 0


@pytest.mark.django_db
class TestCourseCreateUpdateView:
    def test_course_create_success(self, api_client, make_user):
        category = Category.objects.create(name="Web Development")
        user = make_user(
            email="instructor@example.com",
            password="StrongPass123!",
            is_verified=True,
            role=User.Role.INSTRUCTOR,
        )
        api_client.force_authenticate(user=user)

        payload = {
            "title": "New Course",
            "subtitle": "Subtitle",
            "description_rich": "<p>Description</p>",
            "requirements": ["Requirement 1", "Requirement 2"],
            "what_you_will_learn": ["Learn 1", "Learn 2"],
            "category": category.id,
            "level": "beginner",
            "language": "English",
            "price": 100.00,
            "status": "draft",
        }

        response = api_client.post(
            reverse("course-create-update"), payload, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get("toast_type") == ToastType.SUCCESS
        assert response.data.get("slug") is not None

    def test_course_create_unauthenticated(self, api_client):
        payload = {
            "title": "New Course",
            "subtitle": "Subtitle",
            "description_rich": "<p>Description</p>",
            "requirements": ["Requirement 1", "Requirement 2"],
            "what_you_will_learn": ["Learn 1", "Learn 2"],
            "category": 1,
            "level": "beginner",
            "language": "English",
            "price": 100.00,
            "status": "draft",
        }

        response = api_client.post(
            reverse("course-create-update"), payload, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_course_create_forbidden_for_student(self, api_client, make_user):
        category = Category.objects.create(name="Design")
        user = make_user(
            email="student@example.com",
            password="StrongPass123!",
            is_verified=True,
            role=User.Role.STUDENT,
        )
        api_client.force_authenticate(user=user)

        payload = {
            "title": "Student Course",
            "category": category.id,
        }

        response = api_client.post(
            reverse("course-create-update"), payload, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_course_create_invalid_data(self, api_client, make_user):
        category = Category.objects.create(name="Data Science")
        user = make_user(
            email="instructor@example.com",
            password="StrongPass123!",
            is_verified=True,
            role=User.Role.INSTRUCTOR,
        )
        api_client.force_authenticate(user=user)

        payload = {
            "title": "",  # Invalid title
            "subtitle": "Subtitle",
            "description_rich": "<p>Description</p>",
            "requirements": ["Requirement 1", "Requirement 2"],
            "what_you_will_learn": ["Learn 1", "Learn 2"],
            "category": category.id,
            "level": "beginner",
            "language": "English",
            "price": 100.00,
            "status": "draft",
        }

        response = api_client.post(
            reverse("course-create-update"), payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("toast_type") == ToastType.ERROR
        error_fields = [item["field"] for item in response.data.get("errors", [])]
        assert "title" in error_fields
