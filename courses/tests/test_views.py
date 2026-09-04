import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from core.models import ToastType
from courses.models import Category, Course, Lecture, Section
from media_processing.models import VideoAsset
from user_management.models import User


@pytest.fixture
def instructor(make_user):
    return make_user(
        email="instructor@example.com",
        password="StrongPass123!",
        is_verified=True,
        role=User.Role.INSTRUCTOR,
    )


@pytest.fixture
def other_instructor(make_user):
    return make_user(
        email="other_instructor@example.com",
        password="StrongPass123!",
        is_verified=True,
        role=User.Role.INSTRUCTOR,
    )


@pytest.fixture
def student(make_user):
    return make_user(
        email="student@example.com",
        password="StrongPass123!",
        is_verified=True,
        role=User.Role.STUDENT,
    )


@pytest.fixture
def category():
    return Category.objects.create(name="Web Development")


@pytest.fixture
def published_course(instructor, category):
    return Course.objects.create(
        instructor=instructor,
        category=category,
        title="Django & React Bootcamp",
        subtitle="Build modern web apps",
        description="Comprehensive web development",
        description_rich="<p>Comprehensive web development</p>",
        requirements=["Basic Python"],
        what_you_will_learn=["Full Stack Apps"],
        level=Course.Level.BEGINNER,
        language="English",
        price=49.99,
        status=Course.Status.PUBLISHED,
    )


# ---------------------------------------------------------------------------
# Public Views Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCategoryListView:
    def test_category_list_success(self, api_client):
        Category.objects.create(name="Category 1")
        Category.objects.create(name="Category 2")

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
class TestPublicCourseViews:
    def test_public_course_list_only_published(self, api_client, instructor, category, published_course):
        # Create a draft course that should NOT appear in public list
        Course.objects.create(
            instructor=instructor,
            category=category,
            title="Unpublished Draft Course",
            status=Course.Status.DRAFT,
        )

        response = api_client.get(reverse("course-list"))
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", [])
        assert len(results) == 1
        assert results[0]["title"] == published_course.title

    def test_public_course_list_filter_by_category(self, api_client, instructor, category, published_course):
        other_cat = Category.objects.create(name="Design")
        Course.objects.create(
            instructor=instructor,
            category=other_cat,
            title="Figma Masterclass",
            status=Course.Status.PUBLISHED,
        )

        response = api_client.get(reverse("course-list"), {"category": category.slug})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", [])
        assert len(results) == 1
        assert results[0]["title"] == "Django & React Bootcamp"

    def test_public_course_list_search(self, api_client, published_course):
        response = api_client.get(reverse("course-list"), {"search": "React"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", [])
        assert len(results) == 1
        assert results[0]["slug"] == published_course.slug

    def test_public_course_detail_curriculum(self, api_client, published_course):
        section = Section.objects.create(course=published_course, title="Getting Started", order=1)
        video_asset = VideoAsset.objects.create(
            original_file=SimpleUploadedFile("dummy.mp4", b"dummy video content", content_type="video/mp4"),
            status=VideoAsset.Status.READY,
            duration_seconds=120,
        )
        Lecture.objects.create(
            section=section,
            title="Welcome Video",
            content_type=Lecture.ContentType.VIDEO,
            order=1,
            is_preview=True,
            video_asset=video_asset,
        )
        Lecture.objects.create(
            section=section,
            title="Course Syllabus",
            content_type=Lecture.ContentType.PDF,
            order=2,
            is_preview=False,
        )

        response = api_client.get(reverse("course-detail", kwargs={"slug": published_course.slug}))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["title"] == published_course.title
        assert len(data["sections"]) == 1

        lectures = data["sections"][0]["lectures"]
        assert len(lectures) == 2
        # Preview lecture exposes stream URL
        assert lectures[0]["is_preview"] is True
        assert lectures[0]["stream_url"] is not None
        # Non-preview lecture hides stream URL
        assert lectures[1]["is_preview"] is False
        assert lectures[1]["stream_url"] is None

    def test_public_course_detail_draft_returns_404_for_student(self, api_client, instructor, category, student):
        draft_course = Course.objects.create(
            instructor=instructor,
            category=category,
            title="Hidden Draft",
            status=Course.Status.DRAFT,
        )
        api_client.force_authenticate(user=student)
        response = api_client.get(reverse("course-detail", kwargs={"slug": draft_course.slug}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Instructor Course CRUD Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInstructorCourseCRUD:
    def test_course_create_success(self, api_client, instructor, category):
        api_client.force_authenticate(user=instructor)

        payload = {
            "title": "New Python Masterclass",
            "subtitle": "From Zero to Hero",
            "description_rich": "<p>Learn Python</p>",
            "requirements": ["Computer"],
            "what_you_will_learn": ["Python fundamentals"],
            "category": category.id,
            "level": "beginner",
            "language": "English",
            "price": 99.00,
            "status": "draft",
        }

        response = api_client.post(reverse("instructor-course-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["toast_type"] == ToastType.SUCCESS
        assert response.data["slug"] is not None

        course = Course.objects.get(slug=response.data["slug"])
        assert course.instructor == instructor
        assert course.description == "Learn Python"

    def test_course_create_unauthenticated(self, api_client, category):
        payload = {"title": "New Course", "category": category.id}
        response = api_client.post(reverse("instructor-course-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_course_create_forbidden_for_student(self, api_client, student, category):
        api_client.force_authenticate(user=student)
        payload = {"title": "Student Course", "category": category.id}
        response = api_client.post(reverse("instructor-course-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_course_list(self, api_client, instructor, other_instructor, category):
        Course.objects.create(instructor=instructor, category=category, title="Course 1")
        Course.objects.create(instructor=instructor, category=category, title="Course 2")
        Course.objects.create(instructor=other_instructor, category=category, title="Other Course")

        api_client.force_authenticate(user=instructor)
        response = api_client.get(reverse("instructor-course-list-create"))
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", [])
        assert len(results) == 2

    def test_instructor_course_retrieve_and_update(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)

        # Retrieve
        url = reverse("instructor-course-detail", kwargs={"slug": published_course.slug})
        get_res = api_client.get(url)
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.data["title"] == published_course.title

        # Update
        patch_res = api_client.patch(url, {"title": "Updated Title"}, format="json")
        assert patch_res.status_code == status.HTTP_200_OK
        published_course.refresh_from_db()
        assert published_course.title == "Updated Title"

    def test_instructor_course_delete(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)
        url = reverse("instructor-course-detail", kwargs={"slug": published_course.slug})
        del_res = api_client.delete(url)
        assert del_res.status_code == status.HTTP_200_OK
        assert not Course.objects.filter(id=published_course.id).exists()

    def test_other_instructor_cannot_modify_course(self, api_client, other_instructor, published_course):
        api_client.force_authenticate(user=other_instructor)
        url = reverse("instructor-course-detail", kwargs={"slug": published_course.slug})
        res = api_client.patch(url, {"title": "Hacked Title"}, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Instructor Section CRUD & Reordering Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInstructorSectionCRUD:
    def test_create_sections_auto_order(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)
        url = reverse("instructor-section-list-create", kwargs={"course_slug": published_course.slug})

        res1 = api_client.post(url, {"title": "Section One"}, format="json")
        assert res1.status_code == status.HTTP_201_CREATED
        assert res1.data["data"]["order"] == 1

        res2 = api_client.post(url, {"title": "Section Two"}, format="json")
        assert res2.status_code == status.HTTP_201_CREATED
        assert res2.data["data"]["order"] == 2

    def test_update_and_delete_section(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)
        section = Section.objects.create(course=published_course, title="Original Section", order=1)

        url = reverse(
            "instructor-section-detail",
            kwargs={"course_slug": published_course.slug, "pk": section.id},
        )
        patch_res = api_client.patch(url, {"title": "Renamed Section"}, format="json")
        assert patch_res.status_code == status.HTTP_200_OK
        section.refresh_from_db()
        assert section.title == "Renamed Section"

        del_res = api_client.delete(url)
        assert del_res.status_code == status.HTTP_200_OK
        assert not Section.objects.filter(id=section.id).exists()

    def test_reorder_sections(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)
        s1 = Section.objects.create(course=published_course, title="Sec 1", order=1)
        s2 = Section.objects.create(course=published_course, title="Sec 2", order=2)

        reorder_url = reverse(
            "instructor-section-reorder",
            kwargs={"course_slug": published_course.slug},
        )
        payload = {
            "items": [
                {"id": s1.id, "order": 2},
                {"id": s2.id, "order": 1},
            ]
        }
        res = api_client.post(reorder_url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK

        s1.refresh_from_db()
        s2.refresh_from_db()
        assert s1.order == 2
        assert s2.order == 1


# ---------------------------------------------------------------------------
# Instructor Lecture CRUD, Video Upload & Reordering Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInstructorLectureCRUD:
    def test_create_and_reorder_lectures(self, api_client, instructor, published_course):
        api_client.force_authenticate(user=instructor)
        section = Section.objects.create(course=published_course, title="Module 1", order=1)

        create_url = reverse(
            "instructor-lecture-list-create",
            kwargs={"course_slug": published_course.slug, "section_id": section.id},
        )

        res1 = api_client.post(
            create_url,
            {"title": "Lecture 1", "content_type": "video", "is_preview": True},
            format="json",
        )
        assert res1.status_code == status.HTTP_201_CREATED
        lec1_id = res1.data["data"]["id"]
        assert res1.data["data"]["order"] == 1

        res2 = api_client.post(
            create_url,
            {"title": "Lecture 2", "content_type": "pdf"},
            format="json",
        )
        assert res2.status_code == status.HTTP_201_CREATED
        lec2_id = res2.data["data"]["id"]
        assert res2.data["data"]["order"] == 2

        # Reorder lectures
        reorder_url = reverse(
            "instructor-lecture-reorder",
            kwargs={"course_slug": published_course.slug, "section_id": section.id},
        )
        payload = {
            "items": [
                {"id": lec1_id, "order": 2},
                {"id": lec2_id, "order": 1},
            ]
        }
        reorder_res = api_client.post(reorder_url, payload, format="json")
        assert reorder_res.status_code == status.HTTP_200_OK

        l1 = Lecture.objects.get(id=lec1_id)
        l2 = Lecture.objects.get(id=lec2_id)
        assert l1.order == 2
        assert l2.order == 1

    def test_upload_video_dispatches_task(self, api_client, instructor, published_course, mocker):
        mock_task = mocker.patch("courses.views.process_video_asset.delay")

        api_client.force_authenticate(user=instructor)
        section = Section.objects.create(course=published_course, title="Module 1", order=1)
        lecture = Lecture.objects.create(
            section=section, title="Intro Video", content_type="video", order=1
        )

        upload_url = reverse(
            "instructor-lecture-video-upload",
            kwargs={"course_slug": published_course.slug, "pk": lecture.id},
        )

        video_content = b"fake video byte stream content"
        video_file = SimpleUploadedFile("sample.mp4", video_content, content_type="video/mp4")

        res = api_client.post(upload_url, {"video_file": video_file}, format="multipart")
        assert res.status_code == status.HTTP_202_ACCEPTED
        assert res.data["toast_type"] == ToastType.SUCCESS

        lecture.refresh_from_db()
        assert lecture.video_asset is not None
        assert lecture.video_asset.status == VideoAsset.Status.PENDING
        mock_task.assert_called_once_with(lecture.video_asset.id)


# ---------------------------------------------------------------------------
# Video Streaming Tests (Range Requests & Access Control)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVideoStreaming:
    def test_stream_preview_lecture_unauthenticated_with_range(self, api_client, published_course):
        section = Section.objects.create(course=published_course, title="Free Preview Section", order=1)
        video_content = b"0123456789ABCDEF"  # 16 bytes
        video_asset = VideoAsset.objects.create(
            original_file=SimpleUploadedFile("test_preview.mp4", video_content, content_type="video/mp4"),
            status=VideoAsset.Status.READY,
            duration_seconds=60,
        )
        lecture = Lecture.objects.create(
            section=section,
            title="Preview Video",
            content_type="video",
            order=1,
            is_preview=True,
            video_asset=video_asset,
        )

        stream_url = reverse(
            "course-lecture-stream",
            kwargs={"course_slug": published_course.slug, "lecture_id": lecture.id},
        )

        # Unauthenticated request with byte range 0-5
        response = api_client.get(stream_url, HTTP_RANGE="bytes=0-5")
        assert response.status_code == 206
        assert response["Content-Range"] == "bytes 0-5/16"
        assert response["Accept-Ranges"] == "bytes"
        content = b"".join(response.streaming_content)
        assert content == b"012345"

    def test_stream_non_preview_lecture_forbidden_for_student(self, api_client, published_course, student):
        section = Section.objects.create(course=published_course, title="Locked Section", order=1)
        video_asset = VideoAsset.objects.create(
            original_file=SimpleUploadedFile("locked.mp4", b"secret video", content_type="video/mp4"),
            status=VideoAsset.Status.READY,
        )
        lecture = Lecture.objects.create(
            section=section,
            title="Paid Video",
            content_type="video",
            order=1,
            is_preview=False,
            video_asset=video_asset,
        )

        stream_url = reverse(
            "course-lecture-stream",
            kwargs={"course_slug": published_course.slug, "lecture_id": lecture.id},
        )

        # Student should be forbidden from streaming non-preview lecture
        api_client.force_authenticate(user=student)
        res = api_client.get(stream_url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_stream_non_preview_lecture_allowed_for_course_owner(self, api_client, instructor, published_course):
        section = Section.objects.create(course=published_course, title="My Course Section", order=1)
        video_asset = VideoAsset.objects.create(
            original_file=SimpleUploadedFile("instructor.mp4", b"my lecture video", content_type="video/mp4"),
            status=VideoAsset.Status.READY,
        )
        lecture = Lecture.objects.create(
            section=section,
            title="My Video",
            content_type="video",
            order=1,
            is_preview=False,
            video_asset=video_asset,
        )

        stream_url = reverse(
            "course-lecture-stream",
            kwargs={"course_slug": published_course.slug, "lecture_id": lecture.id},
        )

        # Course owner instructor is allowed to stream their own video
        api_client.force_authenticate(user=instructor)
        res = api_client.get(stream_url)
        assert res.status_code == 200
