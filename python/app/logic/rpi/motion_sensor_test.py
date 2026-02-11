import RPi.GPIO as GPIO
import time

PIR_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def motion_detected(channel):
    if GPIO.input(PIR_PIN):
        print("Motion detected")
    else:
        print("Motion ended")

GPIO.add_event_detect(
    PIR_PIN,
    GPIO.BOTH,
    callback=motion_detected,
    bouncetime=200
)

try:
    print("PIR armed")
    while True:
        time.sleep(1)  

except KeyboardInterrupt:
    GPIO.cleanup()