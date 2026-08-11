from django.urls import path

from courses.views import CategoryListView

courses_urlpatterns_v1 = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
]
