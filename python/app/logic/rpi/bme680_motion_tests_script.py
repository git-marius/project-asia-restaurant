# test_combined_sensors.py
import time
import bme680_sensor
import motion_sensor  # your PIR module

# Initialize BME680
sensor = bme680_sensor.init_sensor()

try:
    print("Testing combined sensors...")
    while True:
        bme_data = bme680_sensor.read_sensor(sensor)
        motion = motion_sensor.get_motion_state()
        
        if bme_data:
            print("Temperature:", bme_data['temperature'])
            print("Humidity   :", bme_data['humidity'])
            print("VOC        :", bme_data['gas_resistance'])
        print("Motion detected:", motion)
        print("---")
        time.sleep(1)
except KeyboardInterrupt:
    print("Test stopped")
