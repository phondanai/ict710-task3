from datetime import datetime
from app import db


class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @property
    def serialize(self):
        return {
            "temperature": self.temperature,
            "tiimestamp": self.timestamp,
        }

    def __repr__(self):
        return "<Temperature {}, timestamp {}>".format(self.temperature, self.timestamp)


class Humidity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    humidity = db.Column(db.Float())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @property
    def serialize(self):
        return {
            "humidity": self.humidity,
            "tiimestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return "<Humidity {}, timestamp {}>".format(self.humidity, self.timestamp)


class Sensors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    humidity = db.Column(db.Float())
    temperature = db.Column(db.Float())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    lat = db.Column(db.Float())
    lon = db.Column(db.Float())

    @property
    def serialize(self):
        return {
            "humidity": self.humidity,
            "temperature": self.temperature,
            "temperature": self.lat,
            "temperature": self.lon,
            "tiimestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return "<Humidity {}, Temperature {}, Latitude {}, Longitude {}, timestamp {}>".format(
            self.humidity, self.temperature, self.lat, self.lon, self.timestamp
        )
