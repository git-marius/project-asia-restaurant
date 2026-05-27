from datetime import datetime
from app.extensions.db import db
from app.models import Measurements, VideoRecording


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


def get_video_recordings(limit: int = 25) -> list[VideoRecording]:
    """Gibt die neuesten Videoaufnahmen absteigend nach Aufnahmezeit zurück."""
    return (
        db.session.query(VideoRecording)
        .order_by(VideoRecording.recorded_at.desc(), VideoRecording.id.desc())
        .limit(limit)
        .all()
    )


def get_video_recording(video_id: int) -> VideoRecording | None:
    """Gibt eine Videoaufnahme per ID zurück."""
    return db.session.get(VideoRecording, video_id)
