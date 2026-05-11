from flask import Blueprint, request

from app.common.response import success
from app.services.its_api_service import get_cctv_list
from app.services.detection_service import get_ai_detection_reports


traffic_api_bp = Blueprint("traffic_api", __name__)


@traffic_api_bp.route("/traffic/cctv-list", methods=["GET"])
def traffic_cctv_list():
    region = request.args.get("region", "seoul")
    road_type = request.args.get("roadType", "highway")

    data = get_cctv_list(region=region, road_type=road_type)

    return success(data)


@traffic_api_bp.route("/traffic/ai-events", methods=["GET"])
def traffic_ai_events():
    events = get_ai_detection_reports(limit=10)

    return success(events)