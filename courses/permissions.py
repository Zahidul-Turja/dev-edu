from rest_framework import permissions
from user_management.models import User


def get_course(obj):
    if hasattr(obj, "instructor"):
        return obj
    if hasattr(obj, "course"):
        return obj.course
    if hasattr(obj, "section"):
        return obj.section.course
    if hasattr(obj, "lecture"):
        return obj.lecture.section.course
    raise ValueError(f"Cannot resolve course for {obj}")


class IsInstructorRole(permissions.BasePermission):
    """
    Requires the user to be authenticated and hold an INSTRUCTOR or ADMIN role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.INSTRUCTOR, User.Role.ADMIN)
        )


class IsCourseOwner(permissions.BasePermission):
    """
    Ensures the authenticated user is either staff or the instructor who created the course.
    Works for Course, Section, and Lecture objects via get_course(obj).
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        course = get_course(obj)
        return request.user.is_staff or course.instructor_id == request.user.id
