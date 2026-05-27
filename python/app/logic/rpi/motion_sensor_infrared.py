import RPi.GPIO as GPIO
import time

# Feste Konfiguration for PINs
GPIO.setmode(GPIO.BCM)
PIR_PIN = 18
GPIO.setup(PIR_PIN, GPIO.IN)

def motion_detected():
    return GPIO.input(PIR_PIN)