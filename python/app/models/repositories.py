from datetime import datetime
from app.extensions.db import db
from app.models import Measurements


def get_latest() -> Measurements | None:
    return (
        db.session.query(Measurements)
        .order_by(Measurements.timestamp.desc())
        .first()
    )


def get_since(since: datetime) -> list[Measurements]:
    return (
        db.session.query(Measurements)
        .filter(Measurements.timestamp >= since)
        .order_by(Measurements.timestamp.asc())
        .all()
    )
