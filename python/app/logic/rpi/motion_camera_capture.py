import os


def capture(filename):
    os.system(f"raspivid -o {filename}.h264 -t 5000 -w 320 -h 240 -fps 10 -b 500000")

    
