from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, socketio

from app.routes.health_routes import health_bp
from app.routes.dashboard_api_routes import dashboard_api_bp
from app.routes.traffic_api_routes import traffic_api_bp
from app.routes.ai_detection_routes import ai_detection_bp
from app.routes.route_api_routes import route_api_bp
from app.routes.report_api_routes import report_api_bp
from app.routes.board_api_routes import board_api_bp
from app.routes.assistant_routes import assistant_bp


def create_app():
    app = Flask(__name__, static_folder="static")

    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True
    )

    db.init_app(app)
    socketio.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_api_bp, url_prefix="/api")
    app.register_blueprint(traffic_api_bp, url_prefix="/api")
    app.register_blueprint(ai_detection_bp, url_prefix="/api")
    app.register_blueprint(route_api_bp, url_prefix="/api")
    app.register_blueprint(report_api_bp, url_prefix="/api")
    app.register_blueprint(board_api_bp, url_prefix="/api")
    app.register_blueprint(assistant_bp, url_prefix="/api")

    return app