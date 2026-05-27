try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    GPIO = None


# Feste Konfiguration for PINs
PIR_PIN = 18

if GPIO is not None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)


def motion_detected():
    if GPIO is None:
        return False
    return GPIO.input(PIR_PIN)
