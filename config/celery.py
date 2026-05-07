import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "publish-due-scheduled-posts-every-minute": {
        "task": "social_agent.publish_due_scheduled_posts",
        "schedule": 60.0,
    },
}
