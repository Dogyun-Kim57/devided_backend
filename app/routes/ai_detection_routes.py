from flask import Blueprint, request, Response, current_app, stream_with_context

from app.common.response import success, fail
from app.services.ai_detection_service import analyze_uploaded_file
from app.services.yolo_stream_service import generate_yolo_stream

ai_detection_bp = Blueprint("ai_detection", __name__)


@ai_detection_bp.route("/ai/detect", methods=["POST"])
def detect():
    file = request.files.get("file")

    if not file:
        return fail("분석할 파일이 없습니다.", 400)

    try:
        result = analyze_uploaded_file(file)
        return success(result, "AI 분석이 완료되었습니다.")

    except Exception as e:
        print("[AI DETECTION ERROR]", e)
        return fail("AI 분석 중 오류가 발생했습니다.", 500)


@ai_detection_bp.route("/ai/stream", methods=["GET"])
def ai_stream():
    source = request.args.get("source", "0")

    app = current_app._get_current_object()

    return Response(
        stream_with_context(generate_yolo_stream(source=source, app=app)),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )