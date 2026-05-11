from app.models.route_report import RouteReport
from app.repositories import route_report_repository


def save_route_report(route, origin, destination):
    analysis = route.get("analysis", {})

    report = RouteReport(
        start_name=origin.get("name", "출발지"),
        end_name=destination.get("name", "도착지"),
        distance_text=route.get("distance_text"),
        duration_text=route.get("duration_text"),
        nearby_cctv_count=analysis.get("nearby_cctv_count", 0),
        average_score=analysis.get("average_score", 0),
        risk_level=analysis.get("risk_level", "낮음"),
        comment=analysis.get("comment", "")
    )

    saved = route_report_repository.save(report)

    return convert_report_to_dict(saved)


def get_recent_route_reports(limit=30):
    reports = route_report_repository.find_recent(limit)

    return [
        convert_report_to_dict(report)
        for report in reports
    ]


def convert_report_to_dict(report):
    return {
        "id": report.id,
        "start_name": report.start_name,
        "end_name": report.end_name,
        "distance_text": report.distance_text,
        "duration_text": report.duration_text,
        "nearby_cctv_count": report.nearby_cctv_count,
        "average_score": report.average_score,
        "risk_level": report.risk_level,
        "comment": report.comment,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }