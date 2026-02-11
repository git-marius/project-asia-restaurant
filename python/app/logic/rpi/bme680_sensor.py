import bme680

def init_sensor():
    """Initialize the BME680 sensor and return the sensor object."""
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # Oversampling & filter settings
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

    # Gas heater setup
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    return sensor

def read_sensor(sensor):
    """
    
    {
        'temperature': float,
        'pressure': float,
        'humidity': float,
        'gas_resistance': float (or 0 if not heat stable)
    }
    """
    if sensor.get_sensor_data():
        return {
            'temperature': sensor.data.temperature,
            'pressure': sensor.data.pressure,
            'humidity': sensor.data.humidity,
            'gas_resistance': sensor.data.gas_resistance if sensor.data.heat_stable else 0
        }
    return None


if __name__ == "__main__":
    import time
    sensor = init_sensor()
    try:
        while True:
            data = read_sensor(sensor)
            if data:
                print(data)  # demo
            time.sleep(1)
    except KeyboardInterrupt:
        pass