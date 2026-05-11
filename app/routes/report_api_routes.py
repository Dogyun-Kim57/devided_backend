from flask import Blueprint, request

from app.common.response import success
from app.services.detection_service import get_grouped_detection_reports
from app.services.route_report_service import get_recent_route_reports

report_api_bp = Blueprint("report_api", __name__)


@report_api_bp.route("/reports", methods=["GET"])
def reports_api():
    realtime_page = request.args.get("rt_page", 1, type=int)
    upload_page = request.args.get("up_page", 1, type=int)
    previous_page = request.args.get("prev_page", 1, type=int)

    detection_groups = get_grouped_detection_reports(
        realtime_page=realtime_page,
        upload_page=upload_page,
        previous_page=previous_page,
        limit=300
    )

    route_reports = get_recent_route_reports(limit=30)

    return success({
        "detection_groups": detection_groups,
        "route_reports": route_reports,
    })