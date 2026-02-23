from datetime import datetime
from app.extensions.db import db
from app.models import Measurements


def get_latest() -> Measurements | None:
    """Gibt den neuesten Messwert zurück (oder None, wenn keine Daten existieren)."""
    return (
        db.session.query(Measurements)
        .order_by(Measurements.timestamp.desc())  # neuester Zeitstempel zuerst
        .first()
    )


def get_since(since: datetime) -> list[Measurements]:
    """Gibt alle Messwerte ab einem Zeitpunkt zurück (aufsteigend nach Zeit sortiert)."""
    return (
        db.session.query(Measurements)
        .filter(Measurements.timestamp >= since)  # nur Daten ab 'since'
        .order_by(Measurements.timestamp.asc())   # ältester zuerst
        .all()
    )