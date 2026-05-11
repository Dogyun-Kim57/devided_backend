import os
from datetime import datetime
from werkzeug.utils import secure_filename

from ultralytics import YOLO

from app.extensions import db, socketio
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent

UPLOAD_DIR = "app/static/uploads/detections"
RESULT_DIR = "app/static/uploads/detection_results"

model = None


def get_model():
    global model

    if model is None:
        model = YOLO("yolov8n.pt")

    return model


def analyze_uploaded_file(file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    saved_filename = f"{timestamp}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, saved_filename)

    file.save(save_path)

    yolo = get_model()

    results = yolo(save_path)
    result = results[0]

    detected_objects = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]

        detected_objects.append({
            "class_name": class_name,
            "confidence": round(confidence, 3)
        })

    vehicle_count = count_vehicles(detected_objects)
    person_count = count_persons(detected_objects)

    event_type = decide_event_type(vehicle_count, person_count)
    risk_level = decide_risk_level(vehicle_count, person_count)

    annotated_filename = f"result_{saved_filename}"
    annotated_path = os.path.join(RESULT_DIR, annotated_filename)

    annotated_image = result.plot()
    save_annotated_image(annotated_path, annotated_image)

    snapshot_url = f"/static/uploads/detection_results/{annotated_filename}"

    camera = get_default_camera()

    event = DetectionEvent(
        camera_id=camera.id,
        event_type=event_type,
        risk_level=risk_level,
        object_type=make_object_summary(vehicle_count, person_count),
        confidence=get_max_confidence(detected_objects),
        snapshot_url=snapshot_url
    )

    db.session.add(event)
    db.session.commit()

    result_payload = {
        "event_id": event.id,
        "event_type": event.event_type,
        "risk_level": event.risk_level,
        "object_type": event.object_type,
        "confidence": event.confidence,
        "vehicle_count": vehicle_count,
        "person_count": person_count,
        "detected_objects": detected_objects,
        "snapshot_url": snapshot_url,
        "detected_at": event.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
        "message": make_message(event_type, risk_level, vehicle_count, person_count)
    }

    if event.risk_level in ["위험", "긴급"]:
        socketio.emit("ai_alert", result_payload)

    return result_payload


def save_annotated_image(path, image):
    import cv2
    cv2.imwrite(path, image)


def count_vehicles(objects):
    vehicle_classes = {"car", "truck", "bus", "motorcycle"}

    return sum(
        1 for obj in objects
        if obj["class_name"] in vehicle_classes
    )


def count_persons(objects):
    return sum(
        1 for obj in objects
        if obj["class_name"] == "person"
    )


def decide_event_type(vehicle_count, person_count):
    if vehicle_count >= 8:
        return "정체 의심"

    if vehicle_count >= 1:
        return "차량 감지"

    if person_count >= 1:
        return "보행자 감지"

    return "이상징후 없음"


def decide_risk_level(vehicle_count, person_count):
    if vehicle_count >= 12:
        return "긴급"

    if vehicle_count >= 8:
        return "위험"

    if vehicle_count >= 3:
        return "주의"

    if person_count >= 1:
        return "주의"

    return "낮음"


def make_object_summary(vehicle_count, person_count):
    parts = []

    if vehicle_count > 0:
        parts.append(f"vehicle:{vehicle_count}")

    if person_count > 0:
        parts.append(f"person:{person_count}")

    if not parts:
        return "none"

    return ", ".join(parts)


def get_max_confidence(objects):
    if not objects:
        return 0.0

    return max(obj["confidence"] for obj in objects)


def make_message(event_type, risk_level, vehicle_count, person_count):
    if event_type == "정체 의심":
        return f"차량 {vehicle_count}대가 감지되어 정체 가능성이 있습니다. 위험도는 {risk_level}입니다."

    if event_type == "차량 감지":
        return f"차량 {vehicle_count}대가 감지되었습니다. 현재 위험도는 {risk_level}입니다."

    if event_type == "보행자 감지":
        return f"보행자 {person_count}명이 감지되었습니다. 관제 확인이 필요합니다."

    return "특별한 이상징후가 감지되지 않았습니다."


def get_default_camera():
    camera = Camera.query.first()

    if camera:
        return camera

    camera = Camera(
        name="Demo Camera 01",
        location_name="AI 테스트 구간",
        road_name="AI 테스트 도로",
        thumbnail_url="/static/images/placeholder.jpg",
        is_live=True,
        is_active=True,
    )

    db.session.add(camera)
    db.session.commit()

    return camera