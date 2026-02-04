from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app.extensions.db import db


class RoomData(db.Model):
    __tablename__ = 'room_data'  # table name in database

    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    voc = db.Column(db.Float, nullable=False)
    motion = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RoomData id={self.id} temperatur={self.temperatur} luftfeuchtigkeit={self.luftfeuchtigkeit} voc={self.voc} bewegung={self.bewegung} timestamp={self.timestamp}>"



