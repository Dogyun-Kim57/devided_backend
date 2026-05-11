import requests
from flask import current_app


def compute_route(origin, destination):
    api_key = current_app.config.get("KAKAO_REST_API_KEY")

    if not api_key:
        return make_fallback_route(origin, destination)

    url = "https://apis-navi.kakaomobility.com/v1/directions"

    headers = {
        "Authorization": f"KakaoAK {api_key}",
        "Content-Type": "application/json",
    }

    params = {
        "origin": f"{origin['lng']},{origin['lat']}",
        "destination": f"{destination['lng']},{destination['lat']}",
        "priority": "RECOMMEND",
        "car_fuel": "GASOLINE",
        "car_hipass": "false",
        "alternatives": "false",
        "road_details": "false",
        "summary": "false",
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code != 200:
        print("[KAKAO ROUTE ERROR]", response.status_code, response.text[:500])
        return make_fallback_route(origin, destination)

    data = response.json()
    routes = data.get("routes", [])

    if not routes:
        return make_fallback_route(origin, destination)

    route = routes[0]

    if route.get("result_code") != 0:
        return make_fallback_route(origin, destination)

    summary = route.get("summary", {})
    distance = summary.get("distance", 0)
    duration = summary.get("duration", 0)

    path = extract_path(route)

    return {
        "distance_meters": distance,
        "distance_text": format_distance(distance),
        "duration_seconds": duration,
        "duration_text": format_duration(duration),
        "path": path,
    }


def extract_path(route):
    path = []

    sections = route.get("sections", [])

    for section in sections:
        roads = section.get("roads", [])

        for road in roads:
            vertexes = road.get("vertexes", [])

            for i in range(0, len(vertexes), 2):
                lng = vertexes[i]
                lat = vertexes[i + 1]

                path.append({
                    "lat": lat,
                    "lng": lng,
                })

    return path


def make_fallback_route(origin, destination):
    path = [
        {"lat": origin["lat"], "lng": origin["lng"]},
        {
            "lat": (origin["lat"] + destination["lat"]) / 2,
            "lng": (origin["lng"] + destination["lng"]) / 2,
        },
        {"lat": destination["lat"], "lng": destination["lng"]},
    ]

    return {
        "distance_meters": 8200,
        "distance_text": "8.2 km",
        "duration_seconds": 1320,
        "duration_text": "22분",
        "path": path,
    }


def format_distance(meters):
    if meters >= 1000:
        return f"{meters / 1000:.1f} km"

    return f"{meters} m"


def format_duration(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    remain_minutes = minutes % 60

    if hours > 0:
        return f"{hours}시간 {remain_minutes}분"

    return f"{minutes}분"