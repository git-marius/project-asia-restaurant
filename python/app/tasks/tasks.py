import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from celery import shared_task
from redis import Redis

from app.logic.occupancy_estimator import RoomConfig, ModelConfig, Baseline, estimate_people
from app.logic.rpi.motion_camera_capture import capture_mp4
from app.logic.storage.s3 import get_s3_config, upload_video_file
from app.models.services import (
    create_measurements,
    create_video_recording,
    delete_measurements_older_than,
)


logger = logging.getLogger(__name__)

# Redis-Keys für Videoaufnahmen:
# - MOTION_ACTIVE_KEY verhindert mehrere Clips während derselben Bewegungsphase
# - CAPTURE_LOCK_KEY verhindert parallele Aufnahmeprozesse im Worker
MOTION_ACTIVE_KEY = "videos:motion-active"
CAPTURE_LOCK_KEY = "videos:capture-lock"

# Feste Konfiguration für Raum und Modell (wird für die Personen-Schätzung benutzt)
ROOM = RoomConfig(area_m2=180.0, height_m=3.0, ach_per_hour=2.0, v_ref_m3=300.0, ach_ref_per_hour=2.0)
CFG = ModelConfig(weight_gas=0.8, weight_hum=0.2, n_max=125, i_ref_full=0.20, gas_temp_coeff_per_C=0.0)
BASELINE = Baseline(temperature_c=21.0, rh_percent=35.0, gas_resistance_ohm=22000.0)


def _redis_client() -> Redis:
    """Erstellt den Redis-Client aus derselben URL, die Celery als Broker nutzt."""
    return Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"), decode_responses=True)


def _video_duration_seconds() -> int:
    """Liest die Clip-Länge aus der Umgebung; Standard ist 5 Sekunden."""
    return int(os.getenv("VIDEO_CAPTURE_DURATION_SECONDS", "5"))


def _video_object_key(recorded_at: datetime) -> str:
    """Baut den S3-Pfad: videos/YYYY/MM/DD/<timestamp>_<uuid>.mp4."""
    stamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    return f"videos/{recorded_at:%Y/%m/%d}/{stamp}_{uuid4().hex}.mp4"


def _read_motion_sensor() -> bool:
    """Importiert den PIR-Sensor erst zur Laufzeit, damit lokale Imports ohne GPIO funktionieren."""
    from app.logic.rpi.motion_sensor_infrared import motion_detected

    return bool(motion_detected())


@shared_task(bind=True, name="measurements.read_job")
def read_job(self):
    """Liest Sensordaten, schätzt Personenanzahl und speichert einen Messwert in der DB."""
    logger.info("Task %s started: measurements.read_job", self.request.id)

    try:
        from app.logic.rpi.bme680 import get_sensor_data

        data = get_sensor_data()  # Sensor auslesen
        temp = data["temperature"]
        hum = data["humidity"]
        voc = data["voc"]
        motion = data["motion"]

        # Personenanzahl aus Klima-/VOC-Werten berechnen
        persons = estimate_people(
            temperature_c=temp,
            rh_percent=hum,
            gas_resistance_ohm=voc,
            baseline=BASELINE,
            cfg=CFG,
            room=ROOM,
        )

        # Messwert in DB speichern
        measurement_id = create_measurements(
            temperature=temp,
            humidity=hum,
            voc=voc,
            persons=persons,
            radar=motion,
        )

        logger.info(
            "Task %s finished: measurement_id=%s temp=%s hum=%s voc=%s persons=%s motion=%s",
            self.request.id,
            measurement_id,
            temp,
            hum,
            voc,
            persons,
            motion,
        )

        return {"status": "ok", "measurement_id": measurement_id, "persons": persons, "motion": motion}
    except Exception:
        logger.exception("Task %s failed: measurements.read_job", self.request.id)
        raise


@shared_task(bind=True, name="measurements.delete_old")
def delete_job(self, days: int = 30):
    """Löscht Messwerte, die älter als X Tage sind (Standard: 30)."""
    logger.info("Task %s started: delete_job(days=%s)", self.request.id, days)
    try:
        deleted = delete_measurements_older_than(days=days)
        logger.info("Task %s finished: deleted=%s", self.request.id, deleted)
        return {"status": "ok", "deleted": deleted, "days": days}
    except Exception:
        logger.exception("Task %s failed: delete_job(days=%s)", self.request.id, days)
        raise


@shared_task(bind=True, name="videos.capture_on_motion")
def capture_on_motion(self):
    """Nimmt pro zusammenhängender Bewegung genau einen Clip auf und lädt ihn nach S3."""
    logger.info("Task %s started: videos.capture_on_motion", self.request.id)
    redis_client = _redis_client()
    duration_seconds = _video_duration_seconds()

    try:
        # Keine Bewegung: Bewegungsphase beenden, damit die nächste Bewegung wieder aufnehmen darf.
        if not _read_motion_sensor():
            redis_client.delete(MOTION_ACTIVE_KEY)
            return {"status": "idle", "motion": False}

        # Bewegung läuft schon: keinen weiteren Clip für dieselbe Bewegungsphase starten.
        if redis_client.get(MOTION_ACTIVE_KEY):
            return {"status": "already_active", "motion": True}

        # Lock schützt vor parallelen Worker-Prozessen und überlappenden Kamera-Aufnahmen.
        lock = redis_client.lock(
            CAPTURE_LOCK_KEY,
            timeout=max(duration_seconds + 30, 60),
            blocking_timeout=0,
        )
        if not lock.acquire(blocking=False):
            return {"status": "locked", "motion": True}

        recorded_at = datetime.now(timezone.utc)
        config = get_s3_config()
        object_key = _video_object_key(recorded_at)

        try:
            # Zweite Prüfung nach Lock-Acquire, falls ein anderer Worker schneller war.
            if redis_client.get(MOTION_ACTIVE_KEY):
                return {"status": "already_active", "motion": True}

            # Status bleibt gesetzt, bis der Sensor wieder "keine Bewegung" meldet.
            redis_client.set(MOTION_ACTIVE_KEY, "1", ex=max(duration_seconds + 3600, 3600))

            # Video nur temporär lokal halten; danach wird es nach S3/MinIO geladen.
            with TemporaryDirectory() as tmp_dir:
                output_path = Path(tmp_dir) / "capture.mp4"
                capture_mp4(output_path, duration_seconds=duration_seconds)
                size_bytes = output_path.stat().st_size
                bucket = upload_video_file(output_path, object_key=object_key, content_type="video/mp4")

            # In MariaDB nur Metadaten speichern; die Videodatei liegt im privaten Bucket.
            recording_id = create_video_recording(
                recorded_at=recorded_at,
                duration_seconds=duration_seconds,
                bucket=bucket,
                object_key=object_key,
                content_type="video/mp4",
                size_bytes=size_bytes,
                status="stored",
            )

            return {
                "status": "stored",
                "motion": True,
                "video_recording_id": recording_id,
                "bucket": bucket,
                "object_key": object_key,
            }
        except Exception as exc:
            # Fehlerhafte Aufnahme/Upload trotzdem als failed-Eintrag sichtbar machen.
            create_video_recording(
                recorded_at=recorded_at,
                duration_seconds=duration_seconds,
                bucket=config.bucket,
                object_key=object_key,
                content_type="video/mp4",
                size_bytes=None,
                status="failed",
                error_message=str(exc)[:2000],
            )
            raise
        finally:
            try:
                lock.release()
            except Exception:
                logger.debug("Capture lock was already released or expired", exc_info=True)
    except Exception:
        logger.exception("Task %s failed: videos.capture_on_motion", self.request.id)
        raise
