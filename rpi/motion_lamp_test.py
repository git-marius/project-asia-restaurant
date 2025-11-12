import RPi.GPIO as GPIO
import time
sensor_pin = 26
led_pin = 20
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN)
GPIO.setup(led_pin, GPIO.OUT)

try:
    while True:
        val = GPIO.input(sensor_pin)
        print(val, end="\r")

        if val == 1:
             GPIO.output(led_pin, GPIO.HIGH)
        else:
            GPIO.output(led_pin, GPIO.LOW)
        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()