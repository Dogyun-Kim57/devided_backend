from flask import Blueprint, request

from app.common.response import success, fail
from app.services.kakao_route_service import compute_route
from app.services.route_analysis_service import analyze_route_congestion
from app.services.route_report_service import save_route_report

route_api_bp = Blueprint("route_api", __name__)


@route_api_bp.route("/route/compute", methods=["POST"])
def route_compute():
    data = request.get_json() or {}

    origin = data.get("origin")
    destination = data.get("destination")

    if not origin or not destination:
        return fail("origin and destination are required", 400)

    try:
        route = compute_route(origin, destination)
        analysis = analyze_route_congestion(route.get("path", []))

        route["analysis"] = analysis

        report = save_route_report(route, origin, destination)
        route["report"] = report

        return success(route)

    except Exception as e:
        print("[ROUTE COMPUTE ERROR]", e)
        return fail("경로 계산 및 레포트 저장에 실패했습니다.", 500)