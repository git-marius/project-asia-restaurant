
from gpiozero import DigitalInputDevice
from signal import pause
from datetime import datetime

sensor = DigitalInputDevice(37)

def motion_detected():
    print("motion")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Motion at {now}")


def motion_stopped():
    print("no motion")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Motion stopped at {now}")

sensor.when_activated = motion_detected
sensor.when_deactivated = motion_stopped
