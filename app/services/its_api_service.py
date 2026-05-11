import random


def get_cctv_list(region="seoul", road_type="highway"):
    """
    데모용 CCTV 목록.
    실제 ITS API 연동 전에는 fallback 데이터로 프론트 화면을 안정적으로 테스트한다.
    """

    region_label_map = {
        "seoul": "서울",
        "gyeonggi": "경기",
        "daejeon": "대전",
        "gangwon": "강원",
        "daegu": "대구",
        "gwangju": "광주",
        "busan": "부산",
        "capital": "수도권",
    }

    base_lat_lng = {
        "seoul": (37.5665, 126.9780),
        "gyeonggi": (37.2636, 127.0286),
        "daejeon": (36.3504, 127.3845),
        "gangwon": (37.8813, 127.7298),
        "daegu": (35.8714, 128.6014),
        "gwangju": (35.1595, 126.8526),
        "busan": (35.1796, 129.0756),
        "capital": (37.5665, 126.9780),
    }

    label = region_label_map.get(region, "서울")
    base_lat, base_lng = base_lat_lng.get(region, base_lat_lng["seoul"])

    cctvs = []

    for i in range(1, 13):
        avg_speed = random.choice([18, 25, 38, 45, 62, 75])
        vehicle_count = random.choice([4, 7, 11, 16, 22, 28])

        if avg_speed <= 25 or vehicle_count >= 22:
            status = "정체"
        elif avg_speed <= 45 or vehicle_count >= 15:
            status = "주의"
        else:
            status = "원활"

        cctvs.append({
            "id": i,
            "name": f"{label} CCTV {i:02d}",
            "location_name": f"{label} 관제 구간 {i}",
            "road_name": f"{label} {'터널' if road_type == 'tunnel' else '도로'} {i}",
            "lat": base_lat + (i * 0.008),
            "lng": base_lng + (i * 0.008),
            "status": status,
            "avg_speed": avg_speed,
            "vehicle_count": vehicle_count,
            "cctv_url": "",
            "thumbnail_url": "",
            "is_live": True,
        })

    return cctvs