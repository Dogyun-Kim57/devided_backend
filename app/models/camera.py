from datetime import datetime
from app.extensions import db


class Camera(db.Model):
    __tablename__ = "cameras"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    location_name = db.Column(db.String(100), nullable=False)

    road_name = db.Column(db.String(150), nullable=True)

    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

    stream_url = db.Column(db.String(500), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)

    avg_speed = db.Column(db.Integer, default=0)
    vehicle_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="원활")

    is_active = db.Column(db.Boolean, default=True)
    is_live = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)