import os
# Funktion zum Aufnehmen eines Videos mit der Raspberry-Pi-Kamera
    # Führt den raspivid-Befehl aus:
    # -o       : Ausgabedatei
    # -t 5000  : Aufnahmezeit in Millisekunden (5 Sekunden)
    # -w 320   : Breite des Videos
    # -h 240   : Höhe des Videos
    # -fps 10  : Bilder pro Sekunde
    # -b 500000: Bitrate für die Videoqualität
def capture(filename):
    os.system(f"raspivid -o {filename}.h264 -t 10000 -w 320 -h 240 -fps 10 -b 500000")

    
