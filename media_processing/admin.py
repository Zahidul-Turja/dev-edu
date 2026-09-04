from django.contrib import admin
from media_processing.models import VideoAsset, VideoRendition


class VideoRenditionInline(admin.TabularInline):
    model = VideoRendition
    extra = 0


@admin.register(VideoAsset)
class VideoAssetAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "duration_seconds", "source_height", "created_at"]
    list_filter = ["status"]
    search_fields = ["original_file"]
    inlines = [VideoRenditionInline]
