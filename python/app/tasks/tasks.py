import logging
from app.celery_app import celery
from app.models.services import create_measurements, delete_measurements_older_than
from app.logic.occupancy_estimator import RoomConfig, ModelConfig, Baseline, estimate_people
from app.logic.rpi.bme680_RCWL_data import get_sensor_data

logger = logging.getLogger(__name__)

ROOM = RoomConfig(area_m2=180.0, height_m=3.0, ach_per_hour=2.0, v_ref_m3=300.0, ach_ref_per_hour=2.0)
CFG = ModelConfig(weight_gas=0.8, weight_hum=0.2, n_max=125, i_ref_full=0.20, gas_temp_coeff_per_C=0.0)
BASELINE = Baseline(temperature_c=21.0, rh_percent=35.0, gas_resistance_ohm=22000.0)

@celery.task(bind=True, name="measurements.read_job")
def read_job(self):
    logger.info("Task %s started: measurements.read_job", self.request.id)

    try:
        data = get_sensor_data()
        temp = data["temperature"]
        hum = data["humidity"]
        voc = data["voc"]
        motion = data["motion"]
        
        persons = estimate_people(
            temperature_c=temp,
            rh_percent=hum,
            gas_resistance_ohm=voc,
            baseline=BASELINE,
            cfg=CFG,
            room=ROOM,
        )

        measurement_id = create_measurements(
            temperature=temp,
            humidity=hum,
            voc=voc,
            persons=persons,
            radar=motion,
        )

        logger.info(
            "Task %s finished: measurement_id=%s temp=%s hum=%s voc=%s persons=%s motion=%s",
            self.request.id, measurement_id, temp, hum, voc, persons, motion
        )

        return {
            "status": "ok",
            "measurement_id": measurement_id,
            "persons": persons,
            "motion": motion,
        }

    except Exception:
        logger.exception("Task %s failed: measurements.read_job", self.request.id)
        raise


@celery.task(bind=True, name="measurements.delete_old")
def delete_job(self, days: int = 30):
    logger.info("Task %s started: delete_job(days=%s)", self.request.id, days)
    try:
        deleted = delete_measurements_older_than(days=days)
        logger.info("Task %s finished: deleted=%s", self.request.id, deleted)
        return {"status": "ok", "deleted": deleted, "days": days}
    except Exception:
        logger.exception("Task %s failed: delete_job(days=%s)", self.request.id, days)
        raise
