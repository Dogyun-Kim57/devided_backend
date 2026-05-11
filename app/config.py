import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///traffic_demo.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    DETECTION_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", "0.5"))

    KAKAO_MAP_JS_KEY = os.getenv("KAKAO_MAP_JS_KEY")
    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

    ITS_API_KEY = os.getenv("ITS_API_KEY")
    ITS_CCTV_BASE_URL = os.getenv(
        "ITS_CCTV_BASE_URL",
        "https://openapi.its.go.kr:9443/cctvInfo"
    )

    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    DEFAULT_WEATHER_CITY = os.getenv("DEFAULT_WEATHER_CITY", "Seoul")

    API_STATUS = "정상"