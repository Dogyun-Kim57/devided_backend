from app.repositories import camera_repository, detection_repository, route_report_repository
from app.services.camera_service import get_camera_list
from app.services.detection_service import get_recent_events


def get_dashboard_data():
    total_cameras = camera_repository.count_all()
    live_cameras = camera_repository.count_live()
    today_events = detection_repository.count_today()
    total_events = detection_repository.count_all()

    cameras = get_camera_list()
    recent_events = get_recent_events(limit=5)

    reports = route_report_repository.find_recent(limit=50)
    route_total = len(reports)

    if route_total > 0:
        avg_score = sum(r.average_score for r in reports) // route_total
        high = sum(1 for r in reports if r.risk_level == "높음")
        medium = sum(1 for r in reports if r.risk_level == "주의")
        low = sum(1 for r in reports if r.risk_level == "낮음")
    else:
        avg_score = 0
        high = medium = low = 0

    recent_routes = [
        {
            "start": r.start_name,
            "end": r.end_name,
            "risk": r.risk_level,
            "score": r.average_score,
            "time": r.created_at.strftime("%H:%M"),
        }
        for r in reports[:5]
    ]

    charts = {
        "camera_status": {
            "labels": ["운영중", "비활성"],
            "values": [
                live_cameras,
                max(total_cameras - live_cameras, 0)
            ],
        },
        "route_risk": {
            "labels": ["높음", "주의", "낮음"],
            "values": [high, medium, low],
        },
        "recent_route_score": {
            "labels": [
                f"{r.start_name[:6]}→{r.end_name[:6]}"
                for r in reports[:5]
            ],
            "values": [
                r.average_score
                for r in reports[:5]
            ],
        }
    }

    return {
        "summary": {
            "total_cameras": total_cameras,
            "live_cameras": live_cameras,
            "today_events": today_events,
            "total_events": total_events,
        },
        "route_summary": {
            "total": route_total,
            "avg_score": avg_score,
            "high": high,
            "medium": medium,
            "low": low,
        },
        "recent_routes": recent_routes,
        "recent_events": recent_events,
        "cameras": cameras,
        "charts": charts,
    }