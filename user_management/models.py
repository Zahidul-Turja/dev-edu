from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.core.validators import MaxLengthValidator, MinLengthValidator

from core.models import BaseModel
from core import constants

from user_management.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "female"

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    avatar = models.ImageField(
        upload_to="users/avatars/",
        null=True,
        blank=True,
        help_text="user uploaded image",
    )
    avatar_url = models.URLField(null=True, blank=True, help_text="avatar from OAuth")
    about = models.TextField(
        validators=[MaxLengthValidator(2000)], blank=True, null=True
    )
    gender = models.CharField(choices=Gender.choices, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return self.email

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url

        if self.gender == self.Gender.MALE:
            return constants.DEFAULT_AVATAR_MALE
        if self.gender == self.Gender.FEMALE:
            return constants.DEFAULT_AVATAR_FEMALE

        return constants.DEFAULT_AVATAR


class SocialLink(BaseModel):
    class Platform(models.TextChoices):
        LINKEDIN = "linkedin", "LinkedIn"
        GITHUB = "github", "Github"
        YOUTUBE = "youtube", "Youtube"
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"

    user = models.ForeignKey(
        User, related_name="social_links", on_delete=models.CASCADE
    )
    platform = models.CharField(max_length=20, choices=Platform.choices)
    url = models.URLField()

    class Meta:
        db_table = "social_links"

    def __str__(self):
        return f"{self.platform}: {self.url}"


class InstructorApplication(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="instructor_applications"
    )
    bio = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "instructor_applications"
