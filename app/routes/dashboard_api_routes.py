from flask import Blueprint

from app.common.response import success
from app.services.dashboard_service import get_dashboard_data

dashboard_api_bp = Blueprint("dashboard_api", __name__)


@dashboard_api_bp.route("/dashboard", methods=["GET"])
def dashboard_api():
    return success(get_dashboard_data())