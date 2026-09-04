from django.urls import path
from courses.views import (
    CategoryListView,
    PublicCourseListView,
    PublicCourseDetailView,
    LectureStreamView,
    InstructorCourseListCreateView,
    InstructorCourseDetailView,
    InstructorSectionListCreateView,
    InstructorSectionDetailView,
    InstructorSectionReorderView,
    InstructorLectureListCreateView,
    InstructorLectureDetailView,
    InstructorLectureReorderView,
    InstructorLectureVideoUploadView,
)

instructor_urlpatterns_v1 = [
    path("courses/", InstructorCourseListCreateView.as_view(), name="instructor-course-list-create"),
    path("courses/manage/", InstructorCourseListCreateView.as_view(), name="course-create-update"),
    path("courses/<slug:slug>/", InstructorCourseDetailView.as_view(), name="instructor-course-detail"),
    path(
        "courses/<slug:course_slug>/sections/",
        InstructorSectionListCreateView.as_view(),
        name="instructor-section-list-create",
    ),
    path(
        "courses/<slug:course_slug>/sections/reorder/",
        InstructorSectionReorderView.as_view(),
        name="instructor-section-reorder",
    ),
    path(
        "courses/<slug:course_slug>/sections/<int:pk>/",
        InstructorSectionDetailView.as_view(),
        name="instructor-section-detail",
    ),
    path(
        "courses/<slug:course_slug>/sections/<int:section_id>/lectures/",
        InstructorLectureListCreateView.as_view(),
        name="instructor-lecture-list-create",
    ),
    path(
        "courses/<slug:course_slug>/sections/<int:section_id>/lectures/reorder/",
        InstructorLectureReorderView.as_view(),
        name="instructor-lecture-reorder",
    ),
    path(
        "courses/<slug:course_slug>/lectures/<int:pk>/",
        InstructorLectureDetailView.as_view(),
        name="instructor-lecture-detail",
    ),
    path(
        "courses/<slug:course_slug>/lectures/<int:pk>/video/",
        InstructorLectureVideoUploadView.as_view(),
        name="instructor-lecture-video-upload",
    ),
]

student_urlpatterns_v1 = []

courses_urlpatterns_v1 = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("courses/", PublicCourseListView.as_view(), name="course-list"),
    path(
        "courses/<slug:course_slug>/lectures/<int:lecture_id>/stream/",
        LectureStreamView.as_view(),
        name="course-lecture-stream",
    ),
    path("courses/<slug:slug>/", PublicCourseDetailView.as_view(), name="course-detail"),
]
