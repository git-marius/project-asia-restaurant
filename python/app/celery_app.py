import os
from celery import Celery
from app import create_app
from celery.schedules import crontab

def make_celery() -> Celery:
    flask_app = create_app()

    broker = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

    celery = Celery(
        "app",
        broker=broker,
        backend=backend,
    )
    celery.conf.update(
        timezone=os.getenv("TZ", "Europe/Berlin"),
        enable_utc=True,
    )
    celery.autodiscover_tasks(["app.tasks"])
    celery.conf.beat_schedule = {
        "demo-every-minute": {
            "task": "app.tasks.read_task.read_job",
            "schedule": crontab(minute="*"),
        }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery

celery = make_celery()
