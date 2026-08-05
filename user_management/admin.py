from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from user_management.models import User, InstructorApplication, SocialLink


class SocialLinkTabular(admin.TabularInline):
    model = SocialLink
    fields = ["platform", "url"]
    extra = 0


class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "full_name",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
    ]
    list_filter = ["role", "is_verified", "is_active", "auth_provider"]
    search_fields = ["email", "full_name"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "full_name",
                    "role",
                    "auth_provider",
                    "about",
                    "gender",
                    "date_of_birth",
                    "avatar",
                    "avatar_url",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),
            },
        ),
    )
    inlines = [
        SocialLinkTabular,
    ]


admin.site.register(User, UserAdmin)
admin.site.register(InstructorApplication)
