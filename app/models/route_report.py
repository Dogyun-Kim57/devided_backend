from datetime import datetime
from app.extensions import db


class RouteReport(db.Model):
    __tablename__ = "route_reports"

    id = db.Column(db.Integer, primary_key=True)

    start_name = db.Column(db.String(150), nullable=False)
    end_name = db.Column(db.String(150), nullable=False)

    distance_text = db.Column(db.String(50), nullable=True)
    duration_text = db.Column(db.String(50), nullable=True)

    nearby_cctv_count = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(30), nullable=False)

    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)