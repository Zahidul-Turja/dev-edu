from django.urls import path
from courses.views import CategoryListView, CourseCreateUpdateView

instructor_urlpatterns_v1 = []
student_urlpatterns_v1 = []

courses_urlpatterns_v1 = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("courses/", CourseCreateUpdateView.as_view(), name="course-create-update"),
]
