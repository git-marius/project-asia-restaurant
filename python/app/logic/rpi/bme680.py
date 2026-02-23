import time
import app.logic.rpi.bme680_sensor as bme680_sensor
import app.logic.rpi.motion_sensor as motion_sensor

sensor = bme680_sensor.init_sensor()  # Sensor einmalig initialisieren (nicht bei jedem Aufruf neu)


def get_sensor_data():
    """Liest BME680 + Bewegungsmelder aus und gibt ein einheitliches Dict zurück."""
    bme_data = bme680_sensor.read_sensor(sensor)   # Temperatur/Feuchte/Gas lesen
    motion = motion_sensor.get_motion_state()      # aktueller Bewegungsstatus (True/False)

    # Fallback, falls Sensor nichts liefert (z. B. Start/Fehler)
    if bme_data is None:
        bme_data = {"temperature": 0, "humidity": 0, "gas_resistance": 0}

    return {
        "temperature": bme_data["temperature"],
        "humidity": bme_data["humidity"],
        "voc": bme_data["gas_resistance"],  # Gas-Widerstand als VOC-Wert
        "motion": motion,
    }