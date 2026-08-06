import pytest
import fakeredis
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from user_management import services

User = get_user_model()


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.FakeStrictRedis(decode_response=True)
    monkeypatch.setattr(services, "redis_client", fake)
    return fake


@pytest.fixture(autouse=True)
def celery_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(
        email="user@example.com", password="StrongPass123!", is_verified=False, **kwargs
    ):
        return User.objects.create_user(
            email=email, password=password, is_verified=is_verified, **kwargs
        )

    return _make_user
