# core/models.py
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OTPPurpose(models.TextChoices):
    SIGNUP = "signup", "Signup"
    FORGET_PASSWORD = "forget_password", "Forget Password"
