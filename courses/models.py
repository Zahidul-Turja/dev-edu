from django.contrib.postgres.fields import ArrayField
from django.db import models
from core.models import BaseModel
from core.utils import unique_slugify
from user_management.models import User
from media_processing.models import VideoAsset


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.ImageField(upload_to="icons/category/", blank=True, null=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(BaseModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        EXPERT = "expert", "Expert"
        ALL_LEVELS = "all_levels", "All Levels"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED_FOR_REVIEW = "submitted_for_review", "Submitted for review"
        PUBLISHED = "published", "Published"
        DELETED = "deleted", "Deleted"
        REJECTED = "rejected", "Rejected"

    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="courses"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="courses"
    )

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_rich = models.TextField(blank=True)

    requirements = ArrayField(
        models.CharField(max_length=255), default=list, blank=True
    )
    what_you_will_learn = ArrayField(
        models.CharField(max_length=255), default=list, blank=True
    )

    level = models.CharField(
        max_length=20, choices=Level.choices, default=Level.ALL_LEVELS
    )
    language = models.CharField(max_length=50, default="English")
    thumbnail = models.ImageField(
        upload_to="courses/thumbnails/", null=True, blank=True
    )

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "courses"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, slug_field_name="slug")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Section(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="sections"
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = "course_sections"
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lecture(BaseModel):
    class ContentType(models.TextChoices):
        VIDEO = "video", "Video"
        PDF = "pdf", "PDF"

    class VideoStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="lectures"
    )
    content_type = models.CharField(max_length=10, choices=ContentType.choices)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    is_preview = models.BooleanField(default=False)

    video_asset = models.OneToOneField(
        VideoAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lecture",
    )

    pdf_file = models.FileField(upload_to="courses/pdfs/", null=True, blank=True)

    class Meta:
        db_table = "course_lectures"
        ordering = ["order"]
        unique_together = ("section", "order")

    def __str__(self):
        return f"{self.section.title} — {self.title}"


# May add quiz later
