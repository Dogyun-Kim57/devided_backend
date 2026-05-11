from app import create_app
from app.extensions import db
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    camera1 = Camera(
        name="Demo CCTV 01",
        location_name="서울 터널 입구",
        stream_url="",
        thumbnail_url="/static/images/placeholder.jpg",
        is_live=True,
        is_active=True,
    )

    camera2 = Camera(
        name="Demo CCTV 02",
        location_name="강남대로",
        stream_url="",
        thumbnail_url="/static/images/placeholder.jpg",
        is_live=True,
        is_active=True,
    )

    db.session.add_all([camera1, camera2])
    db.session.commit()

    event1 = DetectionEvent(
        camera_id=camera1.id,
        event_type="차량 감지",
        risk_level="주의",
        object_type="vehicle:3",
        confidence=0.91,
        snapshot_url=None,
    )

    event2 = DetectionEvent(
        camera_id=camera2.id,
        event_type="정체 의심",
        risk_level="위험",
        object_type="vehicle:8",
        confidence=0.88,
        snapshot_url=None,
    )

    db.session.add_all([event1, event2])
    db.session.commit()

    print("초기 DB 세팅 완료")