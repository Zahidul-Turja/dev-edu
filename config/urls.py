from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

from config.views import HealthView
from user_management.urls import auth_urlpatterns_v1, user_urlpatterns_v1

api_v1_urls = [
    path("auth/", include(auth_urlpatterns_v1), name="auth_v1"),
    path("me/", include(user_urlpatterns_v1), name="user_v1"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthView.as_view(), name="health"),
    path("api/v1/", include(api_v1_urls), name="api_v1"),
]

if settings.ENVIRONMENT != "production":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "DevEdu API Admin"
admin.site.site_title = "DevEdu Admin Portal"
admin.site.index_title = "Welcome to DevEdu API Admin"
