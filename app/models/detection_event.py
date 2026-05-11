from datetime import datetime
from app.extensions import db


class DetectionEvent(db.Model):
    __tablename__ = "detection_events"

    id = db.Column(db.Integer, primary_key=True)

    camera_id = db.Column(
        db.Integer,
        db.ForeignKey("cameras.id"),
        nullable=False
    )

    event_type = db.Column(db.String(50), nullable=False)
    risk_level = db.Column(db.String(30), nullable=False)

    object_type = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)

    snapshot_url = db.Column(db.String(500), nullable=True)

    detected_at = db.Column(db.DateTime, default=datetime.utcnow)

    camera = db.relationship("Camera", backref="detection_events")