import app.logic.rpi.bme680 as bme680


def init_sensor():
    """Initialisiert den BME680 Sensor (I2C primär/sekundär) und setzt Mess-Parameter."""
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)  # Standard-I2C-Adresse
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)  # Fallback-Adresse

    # Oversampling/Filter: glättet Messwerte und erhöht Genauigkeit (auf Kosten von Zeit)
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)

    # Gas-Messung aktivieren (für VOC/Gas-Widerstand)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)  # Heizer-Temp in °C
    sensor.set_gas_heater_duration(150)     # Heizer-Dauer in ms
    sensor.select_gas_heater_profile(0)

    return sensor


def read_sensor(sensor):
    """Liest Sensordaten aus und gibt sie als Dict zurück (oder None bei fehlenden Daten)."""
    if sensor.get_sensor_data():
        return {
            "temperature": sensor.data.temperature,
            "pressure": sensor.data.pressure,
            "humidity": sensor.data.humidity,
            "gas_resistance": sensor.data.gas_resistance if sensor.data.heat_stable else 0,  # nur stabiler Wert
        }
    return None


if __name__ == "__main__":
    import time

    sensor = init_sensor()
    try:
        while True:
            data = read_sensor(sensor)
            if data:
                print(data)
            time.sleep(1)
    except KeyboardInterrupt:
        pass