from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]


admin.site.site_header = "DevEdu API Admin"
admin.site.site_title = "DevEdu Admin Portal"
admin.site.index_title = "Welcome to DevEdu API Admin"
