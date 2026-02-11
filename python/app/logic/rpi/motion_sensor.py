import RPi.GPIO as GPIO
import time

PIR_PIN = 26
motion_state = False  # False = no motion, True = motion detected

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def motion_detected(channel):
    global motion_state
    if GPIO.input(PIR_PIN):
        motion_state = True
        print("Motion detected")
    else:
        motion_state = False
        print("Motion ended")

GPIO.add_event_detect(
    PIR_PIN,
    GPIO.BOTH,
    callback=motion_detected,
    bouncetime=200
)

def get_motion_state():
    return motion_state

if __name__ == "__main__":
    try:
        print("PIR armed")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()