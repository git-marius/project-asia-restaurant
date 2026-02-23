from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app.extensions.db import db
from datetime import datetime, timezone


class Measurements(db.Model):
    """SQLAlchemy-Modell für einen einzelnen Messwert (Temperatur, Luftfeuchte, VOC, Personen, Radar, Zeit)."""
    __tablename__ = "measurements"

    id = db.Column(db.Integer, primary_key=True)        # eindeutige ID
    temperature = db.Column(db.Float, nullable=False)   # Temperatur in °C
    humidity = db.Column(db.Float, nullable=False)      # Luftfeuchtigkeit in %
    voc = db.Column(db.Float, nullable=False)           # VOC / Gas-Wert (je nach Sensor)
    persons = db.Column(db.Integer, nullable=False)     # geschätzte Personenanzahl
    radar = db.Column(db.Boolean, nullable=False)       # Bewegung erkannt (True/False)

    # Zeitpunkt des Messwerts (Standard: jetzt in UTC)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Hilft beim Debuggen: zeigt wichtige Felder beim Printen des Objekts."""
        return (
            f"<Measurements id={self.id} temperature={self.temperature} humidity={self.humidity} "
            f"voc={self.voc} persons={self.persons} radar={self.radar} timestamp={self.timestamp}>"
        )