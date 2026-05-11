from app.extensions import db
from app.models.route_report import RouteReport


def save(report):
    db.session.add(report)
    db.session.commit()
    return report


def find_recent(limit=30):
    return (
        RouteReport.query
        .order_by(RouteReport.created_at.desc())
        .limit(limit)
        .all()
    )