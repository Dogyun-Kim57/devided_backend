import os
import time
import math
from datetime import datetime

import cv2

from app.extensions import db, socketio
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent

from app.services.ai_detection_service import (
    get_model,
    count_persons,
    make_object_summary,
    get_max_confidence,
    make_message,
)

RESULT_DIR = "app/static/uploads/detection_results"

ANOMALY_SAVE_INTERVAL_SECONDS = 10

DEMO_DANGER_VEHICLE_COUNT = 2
DEMO_EMERGENCY_VEHICLE_COUNT = 4

STATIONARY_MOVE_THRESHOLD = 12
STATIONARY_FRAME_THRESHOLD = 12


class SimpleVehicleTracker:
    def __init__(self):
        self.tracks = {}
        self.next_id = 1

    def update(self, vehicle_boxes):
        stopped_count = 0
        updated_tracks = {}

        for box in vehicle_boxes:
            cx, cy = box["center"]

            matched_id = None
            min_distance = 99999

            for track_id, track in self.tracks.items():
                old_cx, old_cy = track["center"]
                distance = math.sqrt((cx - old_cx) ** 2 + (cy - old_cy) ** 2)

                if distance < min_distance:
                    min_distance = distance
                    matched_id = track_id

            if matched_id is not None and min_distance < 80:
                old_track = self.tracks[matched_id]

                if min_distance <= STATIONARY_MOVE_THRESHOLD:
                    stationary_frames = old_track["stationary_frames"] + 1
                else:
                    stationary_frames = 0

                updated_tracks[matched_id] = {
                    "center": (cx, cy),
                    "stationary_frames": stationary_frames,
                }

                if stationary_frames >= STATIONARY_FRAME_THRESHOLD:
                    stopped_count += 1

            else:
                updated_tracks[self.next_id] = {
                    "center": (cx, cy),
                    "stationary_frames": 0,
                }
                self.next_id += 1

        self.tracks = updated_tracks
        return stopped_count


def parse_video_source(source):
    if source is None or source == "":
        return 0

    if str(source).isdigit():
        return int(source)

    return source


def generate_yolo_stream(source="0", app=None):
    os.makedirs(RESULT_DIR, exist_ok=True)

    video_source = parse_video_source(source)
    cap = cv2.VideoCapture(video_source)

    model = get_model()
    tracker = SimpleVehicleTracker()

    last_saved_at = 0

    try:
        while cap.isOpened():
            success, frame = cap.read()

            if not success:
                print("[YOLO STREAM] 프레임 읽기 실패")
                break

            frame = resize_frame(frame, width=1280)

            results = model(
                frame,
                imgsz=1280,
                conf=0.15,
                verbose=False
            )

            result = results[0]

            detected_objects, vehicle_boxes = parse_detected_objects_and_boxes(result)

            vehicle_count = count_vehicles_from_objects(detected_objects)
            person_count = count_persons(detected_objects)
            stopped_vehicle_count = tracker.update(vehicle_boxes)

            event_type = decide_stream_event_type(vehicle_count, stopped_vehicle_count)
            risk_level = decide_stream_risk_level(vehicle_count, stopped_vehicle_count)

            annotated_frame = result.plot()

            draw_stream_status(
                annotated_frame,
                vehicle_count,
                stopped_vehicle_count,
                event_type,
                risk_level
            )

            now = time.time()

            if risk_level in ["위험", "긴급"]:
                if now - last_saved_at >= ANOMALY_SAVE_INTERVAL_SECONDS:
                    try:
                        save_realtime_anomaly_event(
                            app=app,
                            annotated_frame=annotated_frame,
                            detected_objects=detected_objects,
                            vehicle_count=vehicle_count,
                            person_count=person_count,
                            stopped_vehicle_count=stopped_vehicle_count,
                            event_type=event_type,
                            risk_level=risk_level,
                        )
                    except Exception as e:
                        print("[STREAM SAVE ERROR]", e)

                    last_saved_at = now

            ok, buffer = cv2.imencode(".jpg", annotated_frame)

            if not ok:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            time.sleep(0.03)

    finally:
        cap.release()
        print("[YOLO STREAM] 스트림 종료")


def parse_detected_objects_and_boxes(result):
    detected_objects = []
    vehicle_boxes = []

    vehicle_classes = {"car", "truck", "bus", "motorcycle"}

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]

        detected_objects.append({
            "class_name": class_name,
            "confidence": round(confidence, 3)
        })

        if class_name in vehicle_classes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            vehicle_boxes.append({
                "class_name": class_name,
                "confidence": round(confidence, 3),
                "box": (x1, y1, x2, y2),
                "center": (cx, cy),
            })

    return detected_objects, vehicle_boxes


def count_vehicles_from_objects(objects):
    vehicle_classes = {"car", "truck", "bus", "motorcycle"}

    return sum(
        1 for obj in objects
        if obj["class_name"] in vehicle_classes
    )


def decide_stream_event_type(vehicle_count, stopped_vehicle_count):
    if stopped_vehicle_count >= 1:
        return "정지 차량 의심"

    if vehicle_count >= DEMO_DANGER_VEHICLE_COUNT:
        return "정체 의심"

    if vehicle_count >= 1:
        return "차량 감지"

    return "이상징후 없음"


def decide_stream_risk_level(vehicle_count, stopped_vehicle_count):
    if stopped_vehicle_count >= 1:
        return "위험"

    if vehicle_count >= DEMO_EMERGENCY_VEHICLE_COUNT:
        return "긴급"

    if vehicle_count >= DEMO_DANGER_VEHICLE_COUNT:
        return "위험"

    return "낮음"


def draw_stream_status(frame, vehicle_count, stopped_vehicle_count, event_type, risk_level):
    text = (
        f"{event_type} | Risk: {risk_level} | "
        f"Vehicles: {vehicle_count} | Stopped: {stopped_vehicle_count}"
    )

    cv2.rectangle(frame, (12, 12), (820, 52), (15, 23, 42), -1)
    cv2.putText(
        frame,
        text,
        (24, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )


def get_or_create_default_camera():
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


def save_realtime_anomaly_event(
    app,
    annotated_frame,
    detected_objects,
    vehicle_count,
    person_count,
    stopped_vehicle_count,
    event_type,
    risk_level,
):
    if app is None:
        raise RuntimeError("Flask app 객체가 전달되지 않았습니다.")

    with app.app_context():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"realtime_anomaly_{timestamp}.jpg"
        save_path = os.path.join(RESULT_DIR, filename)

        cv2.imwrite(save_path, annotated_frame)

        snapshot_url = f"/static/uploads/detection_results/{filename}"

        camera = get_or_create_default_camera()

        object_summary = make_object_summary(vehicle_count, person_count)

        if stopped_vehicle_count > 0:
            object_summary += f", stopped_vehicle:{stopped_vehicle_count}"

        event = DetectionEvent(
            camera_id=camera.id,
            event_type=event_type,
            risk_level=risk_level,
            object_type=object_summary,
            confidence=get_max_confidence(detected_objects),
            snapshot_url=snapshot_url
        )

        db.session.add(event)
        db.session.commit()

        payload = {
            "event_id": event.id,
            "id": event.id,
            "event_type": event.event_type,
            "risk_level": event.risk_level,
            "object_type": event.object_type,
            "confidence": event.confidence,
            "vehicle_count": vehicle_count,
            "person_count": person_count,
            "stopped_vehicle_count": stopped_vehicle_count,
            "snapshot_url": snapshot_url,
            "detected_at": event.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message": make_message(event_type, risk_level, vehicle_count, person_count),
            "camera_name": camera.name,
            "location_name": camera.location_name,
        }

        socketio.emit("ai_alert", payload)

        print(
            f"[REALTIME ANOMALY SAVED] "
            f"id={event.id}, type={event.event_type}, risk={event.risk_level}"
        )


def resize_frame(frame, width=1280):
    height, current_width = frame.shape[:2]

    if current_width <= width:
        return frame

    ratio = width / current_width
    new_height = int(height * ratio)

    return cv2.resize(frame, (width, new_height))