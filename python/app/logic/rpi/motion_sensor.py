import RPi.GPIO as GPIO
import time

PIR_PIN = 26
motion_state = False  # globaler Status: False = keine Bewegung, True = Bewegung erkannt

GPIO.setmode(GPIO.BCM)  # BCM-Nummerierung (GPIO-Nummern statt Pin-Nummern)
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Eingang mit Pull-Down (Standard = LOW)


def motion_detected(channel):
    """Callback bei Pegelwechsel am PIR: aktualisiert motion_state."""
    global motion_state
    if GPIO.input(PIR_PIN):
        motion_state = True
        print("Motion detected")
    else:
        motion_state = False
        print("Motion ended")


# Event-Listener: reagiert auf steigende UND fallende Flanke (Bewegung startet/endet)
GPIO.add_event_detect(
    PIR_PIN,
    GPIO.BOTH,
    callback=motion_detected,
    bouncetime=200,  # Entprellen in ms
)


def get_motion_state():
    """Gibt den aktuellen Bewegungsstatus zurück (True/False)."""
    return motion_state


if __name__ == "__main__":
    # Testmodus: Programm läuft und wartet auf Bewegungs-Events
    try:
        print("PIR armed")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()  # GPIO sauber freigeben