from app.repositories import camera_repository


def convert_camera_to_dict(camera):
    return {
        "id": camera.id,
        "name": camera.name,
        "location_name": camera.location_name,
        "road_name": camera.road_name or camera.location_name,
        "lat": camera.lat,
        "lng": camera.lng,
        "stream_url": camera.stream_url,
        "thumbnail_url": camera.thumbnail_url,
        "avg_speed": camera.avg_speed,
        "vehicle_count": camera.vehicle_count,
        "status": camera.status,
        "is_live": camera.is_live,
        "is_active": camera.is_active,
    }


def get_camera_list():
    cameras = camera_repository.find_all()
    return [convert_camera_to_dict(camera) for camera in cameras]