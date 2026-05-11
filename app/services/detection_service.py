from datetime import datetime

from app.repositories import detection_repository

PAGE_SIZE = 7


def classify_event_source(snapshot_url):
    if snapshot_url and "realtime_anomaly_" in snapshot_url:
        return "realtime"

    return "upload"


def convert_event_to_dict(event, confidence_percent=False):
    confidence = event.confidence or 0

    if confidence_percent:
        confidence = round(confidence * 100, 1)

    return {
        "id": event.id,
        "camera_id": event.camera_id,
        "camera_name": event.camera.name if event.camera else "미지정 카메라",
        "location_name": event.camera.location_name if event.camera else "위치 정보 없음",
        "event_type": event.event_type,
        "risk_level": event.risk_level,
        "object_type": event.object_type or "-",
        "confidence": confidence,
        "snapshot_url": event.snapshot_url,
        "detected_at": event.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
        "detected_date": event.detected_at.date(),
        "source_type": classify_event_source(event.snapshot_url),
    }


def paginate_list(items, page, page_size=PAGE_SIZE):
    total_count = len(items)
    total_pages = max((total_count + page_size - 1) // page_size, 1)

    page = max(page, 1)
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }


def get_recent_events(limit=5):
    events = detection_repository.find_recent(limit)

    return [
        convert_event_to_dict(event, confidence_percent=False)
        for event in events
    ]


def get_ai_detection_reports(limit=50):
    events = detection_repository.find_recent(limit)

    return [
        convert_event_to_dict(event, confidence_percent=True)
        for event in events
    ]


def get_grouped_detection_reports(
    realtime_page=1,
    upload_page=1,
    previous_page=1,
    limit=300
):
    today = datetime.now().date()

    events = detection_repository.find_recent_by_risk_levels(
        risk_levels=["위험", "긴급"],
        limit=limit
    )

    realtime_today = []
    upload_today = []
    previous_records = []

    for event in events:
        item = convert_event_to_dict(event, confidence_percent=True)
        is_today = item["detected_date"] == today

        if is_today and item["source_type"] == "realtime":
            realtime_today.append(item)
        elif is_today and item["source_type"] == "upload":
            upload_today.append(item)
        else:
            previous_records.append(item)

    return {
        "realtime_today": paginate_list(realtime_today, realtime_page),
        "upload_today": paginate_list(upload_today, upload_page),
        "previous_records": paginate_list(previous_records, previous_page),
        "summary": {
            "realtime_today_count": len(realtime_today),
            "upload_today_count": len(upload_today),
            "previous_count": len(previous_records),
            "total_count": len(realtime_today) + len(upload_today) + len(previous_records),
        }
    }