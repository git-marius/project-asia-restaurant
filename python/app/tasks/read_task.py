from app.celery_app import celery
from app.extensions.db import db

@celery.task()
def read_job():
    return "ok"
