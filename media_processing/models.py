from django.db import models
from core.models import BaseModel


class VideoAsset(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    original_file = models.FileField(upload_to="videos/originals/")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    source_height = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "video_assets"


class VideoRendition(BaseModel):
    class Resolution(models.TextChoices):
        P480 = "480p", "480p"
        P720 = "720p", "720p"
        P1080 = "1080p", "1080p"

    video_asset = models.ForeignKey(
        VideoAsset, on_delete=models.CASCADE, related_name="renditions"
    )
    resolution = models.CharField(max_length=10, choices=Resolution.choices)
    file = models.FileField(upload_to="videos/renditions/")
    bitrate_kbps = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "video_renditions"
        unique_together = ("video_asset", "resolution")
