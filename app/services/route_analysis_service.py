import math

from app.services.its_api_service import get_cctv_list
from app.services.congestion_service import calculate_congestion_score, get_risk_level


def analyze_route_congestion(route_path):
    cctv_list = get_cctv_list(region="capital")

    nearby_cctvs = []

    for cctv in cctv_list:
        min_distance = get_min_distance_to_route(cctv, route_path)

        if min_distance <= 2.0:
            score = calculate_congestion_score(cctv)

            nearby_cctvs.append({
                "id": cctv.get("id"),
                "name": cctv.get("name"),
                "road_name": cctv.get("road_name"),
                "lat": cctv.get("lat"),
                "lng": cctv.get("lng"),
                "status": cctv.get("status"),
                "avg_speed": cctv.get("avg_speed"),
                "vehicle_count": cctv.get("vehicle_count"),
                "distance_km": round(min_distance, 2),
                "congestion_score": score,
                "risk_level": get_risk_level(score),
            })

    if not nearby_cctvs:
        return {
            "nearby_cctv_count": 0,
            "average_score": 0,
            "risk_level": "낮음",
            "nearby_cctvs": [],
            "comment": "경로 주변에서 분석 가능한 CCTV가 발견되지 않았습니다."
        }

    average_score = sum(item["congestion_score"] for item in nearby_cctvs) // len(nearby_cctvs)
    risk_level = get_risk_level(average_score)

    return {
        "nearby_cctv_count": len(nearby_cctvs),
        "average_score": average_score,
        "risk_level": risk_level,
        "nearby_cctvs": nearby_cctvs[:10],
        "comment": make_route_comment(risk_level, len(nearby_cctvs), average_score),
    }


def get_min_distance_to_route(cctv, route_path):
    cctv_lat = cctv.get("lat")
    cctv_lng = cctv.get("lng")

    if cctv_lat is None or cctv_lng is None:
        return 9999

    if not route_path:
        return 9999

    min_distance = 9999
    sample_path = route_path[::max(1, len(route_path) // 80)]

    for point in sample_path:
        distance = haversine_km(
            cctv_lat,
            cctv_lng,
            point["lat"],
            point["lng"]
        )
        min_distance = min(min_distance, distance)

    return min_distance


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371

    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius * c


def make_route_comment(risk_level, count, score):
    if risk_level == "높음":
        return f"경로 주변에 분석 대상 CCTV {count}개가 있으며, 평균 정체 점수는 {score}점입니다. 일부 구간에서 정체 가능성이 높으므로 우회 경로 검토가 필요합니다."

    if risk_level == "주의":
        return f"경로 주변에 CCTV {count}개가 확인되었고, 평균 정체 점수는 {score}점입니다. 현재는 주의 수준이지만 특정 구간의 흐름을 확인하는 것이 좋습니다."

    return f"경로 주변 CCTV {count}개 기준 평균 정체 점수는 {score}점입니다. 현재 경로는 비교적 원활한 편으로 판단됩니다."