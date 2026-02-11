# test_combined_sensors.py
import time
import bme680_sensor
import motion_sensor  # your PIR module

# Initialize BME680 sensor
sensor = bme680_sensor.init_sensor()

def get_sensor_data():
    """
    Reads both BME680 and PIR sensors and returns a dictionary with:
    {
        'temperature': float,
        'humidity': float,
        'voc': float,
        'motion': bool
    }
    """
    bme_data = bme680_sensor.read_sensor(sensor)
    motion = motion_sensor.get_motion_state()

    if bme_data is None:
        # Provide default values if BME680 fails
        bme_data = {'temperature': 0, 'humidity': 0, 'gas_resistance': 0}

    return {
        'temperature': bme_data['temperature'],
        'humidity': bme_data['humidity'],
        'voc': bme_data['gas_resistance'],
        'motion': motion
    }

