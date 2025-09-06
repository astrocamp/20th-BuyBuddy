import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BuyBuddy.settings")

app = Celery("BuyBuddy")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check_deadline_by_min": {
        "task": "groups.tasks.check_deadline",
        "schedule": crontab(minute=0, hour=0),
    },
}