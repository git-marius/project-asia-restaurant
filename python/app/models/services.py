import logging
from datetime import datetime, timedelta, timezone
from app.extensions.db import db
from app.models.measurements import Measurements

logger = logging.getLogger(__name__)

def create_measurements(temperature, humidity, voc, persons, radar) -> int:
    m = Measurements(
        temperature=temperature,
        humidity=humidity,
        voc=voc,
        persons=persons,
        radar=radar
    )
    try:
        db.session.add(m)
        db.session.commit()
        logger.info("Created measurement id=%s", m.id)
        return m.id
    except Exception:
        db.session.rollback()
        logger.exception("Failed to create measurement")
        raise

def delete_measurements_older_than(days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        deleted_count = (
            db.session.query(Measurements)
            .filter(Measurements.timestamp < cutoff)
            .delete(synchronize_session=False)
        )
        db.session.commit()
        logger.info("Deleted %s measurements older than %s days (cutoff=%s)", deleted_count, days, cutoff)
        return deleted_count
    except Exception:
        db.session.rollback()
        logger.exception("Failed to delete old measurements (days=%s, cutoff=%s)", days, cutoff)
        raise
