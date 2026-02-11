from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app.extensions.db import db


class Measurements(db.Model):
    __tablename__ = 'measurements'

    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    voc = db.Column(db.Float, nullable=False)
    motion = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Measurements id={self.id} temperatur={self.temperatur} luftfeuchtigkeit={self.luftfeuchtigkeit} voc={self.voc} bewegung={self.bewegung} timestamp={self.timestamp}>"



