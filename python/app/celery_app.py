import os
from celery import Celery
from app import create_app
from celery.schedules import crontab


def make_celery() -> Celery:
    """Erstellt eine Celery-Instanz inkl. Flask-App-Context und Beat-Zeitplan."""
    flask_app = create_app()  # Flask-App für App-Context (DB, Config, etc.)

    # Redis als Broker (Jobs) und Backend (Ergebnisse) per Environment konfigurierbar
    broker = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

    celery = Celery("app", broker=broker, backend=backend)

    # Zeitzone/UTC-Verhalten für geplante Jobs
    celery.conf.update(
        timezone=os.getenv("TZ", "Europe/Berlin"),
        enable_utc=True,
    )

    celery.autodiscover_tasks(["app.tasks"])

    # Zeitgesteuerte Jobs (Celery Beat)
    celery.conf.beat_schedule = {
        "read-measurements": {  # alle 5 Minuten Messwerte lesen
            "task": "measurements.read_job TEST",
            "schedule": crontab(minute="*/5"),
            "args": (),
        },
        "delete-old-measurements-daily": {  # täglich um 03:00 alte Daten löschen
            "task": "measurements.delete_old TEST",
            "schedule": crontab(hour=3, minute=0),
            "kwargs": {"days": 30},
        },
    }

    class ContextTask(celery.Task):
        """Sorgt dafür, dass jeder Task innerhalb des Flask-App-Context läuft."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()  # globale Celery-Instanz für Worker/Beat