from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BuyBuddy.settings')

app = Celery("BuyBuddy")

app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL'),
    result_backend='rpc://',
    include=["groups.tasks"]
)

app.conf.timezone = "Asia/Taipei"

app.autodiscover_tasks()

app.conf.beat_schedule = {
	"check_deadline_by_min" : {
		"task": "groups.tasks.check_deadline",
		"schedule": crontab(minute=0, hour=0)
	}
}