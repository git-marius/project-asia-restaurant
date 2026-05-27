import RPi.GPIO as GPIO
import time

# Feste Konfiguration for PINs
GPIO.setmode(GPIO.BCM)
# PIR-Bewegungssensor ist an GPIO-Pin 18 angeschlossen
PIR_PIN = 18
# Pin als Eingang definieren
GPIO.setup(PIR_PIN, GPIO.IN)
# Funktion prüft, ob Bewegung erkannt wurde
def motion_detected():
    return GPIO.input(PIR_PIN)