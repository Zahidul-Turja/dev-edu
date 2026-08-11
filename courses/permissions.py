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

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in (
            User.Role.INSTRUCTOR,
            User.Role.ADMIN,
        )


class IsCourseOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        course = get_course(obj)
        return request.user.is_staff or course.instructor_id == request.user.id
