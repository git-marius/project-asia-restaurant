# test_bme680.py
import time
import bme680_sensor  # your module

# Initialize sensor
sensor = bme680_reader.init_sensor()

try:
    print("Testing BME680 sensor readings...")
    for _ in range(5):  # test 5 readings
        data = bme680_reader.read_sensor(sensor)
        if data:
            print("Temperature:", data['temperature'])
            print("Humidity   :", data['humidity'])
            print("VOC        :", data['gas_resistance'])
            print("---")
        else:
            print("No data yet")
        time.sleep(1)  # short delay between readings

except KeyboardInterrupt:
    print("Test stopped")
