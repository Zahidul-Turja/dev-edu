from django.contrib import admin
from django.urls import path, include

from user_management.urls import auth_urlpatterns_v1

api_v1_urls = [
    path("auth/", include(auth_urlpatterns_v1), name="auth_v1"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_urls), name="api_v1"),
]


admin.site.site_header = "DevEdu API Admin"
admin.site.site_title = "DevEdu Admin Portal"
admin.site.index_title = "Welcome to DevEdu API Admin"
