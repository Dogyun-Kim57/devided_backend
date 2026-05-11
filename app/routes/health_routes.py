from flask import Blueprint
from app.common.response import success

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    return success({
        "status": "ok",
        "server": "backend-server"
    })