import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
# settings.py-ban: CELERY_BROKER_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
