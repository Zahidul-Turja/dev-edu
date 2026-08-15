from django.urls import path
from .views import CategoryListView, CourseCreateUpdateView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("courses/", CourseCreateUpdateView.as_view(), name="course-create-update"),
]
