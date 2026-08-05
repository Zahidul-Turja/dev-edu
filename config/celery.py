import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("devedu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.task_routes = {
    "user_management.tasks.*": {"queue": "default"},
    "media_processing.tasks.*": {"queue": "media"},
}


app.conf.task_default_queue = "default"
