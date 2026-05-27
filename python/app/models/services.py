import logging
from datetime import datetime, timedelta, timezone
from app.extensions.db import db
from app.models.measurements import Measurements
from app.models.video_recording import VideoRecording

logger = logging.getLogger(__name__)


def create_measurements(temperature, humidity, voc, persons, radar) -> int:
    """Legt einen neuen Messwert in der DB an und gibt die erzeugte ID zurück."""
    m = Measurements(
        temperature=temperature,
        humidity=humidity,
        voc=voc,
        persons=persons,
        radar=radar,
    )
    try:
        db.session.add(m)       # Objekt zur Session hinzufügen
        db.session.commit()     # in die DB schreiben
        logger.info("Created measurement id=%s", m.id)
        return m.id
    except Exception:
        db.session.rollback()   # bei Fehler alles zurückrollen
        logger.exception("Failed to create measurement")
        raise


def delete_measurements_older_than(days: int = 30) -> int:
    """Löscht Messwerte, die älter als 'days' sind, und gibt die Anzahl der gelöschten Zeilen zurück."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)  # Stichtag berechnen

    try:
        deleted_count = (
            db.session.query(Measurements)
            .filter(Measurements.timestamp < cutoff)            # nur Datensätze vor dem Stichtag
            .delete(synchronize_session=False)                  # direktes DELETE in SQL
        )
        db.session.commit()
        logger.info("Deleted %s measurements older than %s days (cutoff=%s)", deleted_count, days, cutoff)
        return deleted_count
    except Exception:
        db.session.rollback()
        logger.exception("Failed to delete old measurements (days=%s, cutoff=%s)", days, cutoff)
        raise


def create_video_recording(
    *,
    recorded_at: datetime,
    duration_seconds: int,
    bucket: str,
    object_key: str,
    content_type: str,
    size_bytes: int | None,
    status: str,
    error_message: str | None = None,
) -> int:
    """Speichert Metadaten zu einer Videoaufnahme und gibt die erzeugte ID zurück."""
    recording = VideoRecording(
        recorded_at=recorded_at,
        duration_seconds=duration_seconds,
        bucket=bucket,
        object_key=object_key,
        content_type=content_type,
        size_bytes=size_bytes,
        status=status,
        error_message=error_message,
    )

    try:
        db.session.add(recording)
        db.session.commit()
        logger.info("Created video recording id=%s status=%s", recording.id, status)
        return recording.id
    except Exception:
        db.session.rollback()
        logger.exception("Failed to create video recording")
        raise
