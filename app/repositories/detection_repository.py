from datetime import datetime, timedelta, time
from sqlalchemy import func

from app.extensions import db
from app.models.detection_event import DetectionEvent


def count_all():
    return db.session.query(func.count(DetectionEvent.id)).scalar() or 0


def count_today():
    today = datetime.now().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    return (
        db.session.query(func.count(DetectionEvent.id))
        .filter(DetectionEvent.detected_at >= start)
        .filter(DetectionEvent.detected_at <= end)
        .scalar()
        or 0
    )


def find_recent(limit=10):
    return (
        DetectionEvent.query
        .order_by(DetectionEvent.detected_at.desc())
        .limit(limit)
        .all()
    )


def find_recent_by_risk_levels(risk_levels, limit=100):
    return (
        DetectionEvent.query
        .filter(DetectionEvent.risk_level.in_(risk_levels))
        .order_by(DetectionEvent.detected_at.desc())
        .limit(limit)
        .all()
    )


def get_level_counts():
    result = (
        db.session.query(
            DetectionEvent.risk_level,
            func.count(DetectionEvent.id)
        )
        .group_by(DetectionEvent.risk_level)
        .all()
    )

    return {level or "미분류": count for level, count in result}


def get_hourly_counts():
    since = datetime.now() - timedelta(hours=24)

    result = (
        db.session.query(
            func.strftime("%H", DetectionEvent.detected_at),
            func.count(DetectionEvent.id)
        )
        .filter(DetectionEvent.detected_at >= since)
        .group_by(func.strftime("%H", DetectionEvent.detected_at))
        .all()
    )

    return {hour: count for hour, count in result}