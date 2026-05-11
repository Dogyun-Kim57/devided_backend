def calculate_congestion_score(cctv):
    score = 0

    avg_speed = cctv.get("avg_speed") or 0
    vehicle_count = cctv.get("vehicle_count") or 0
    status = cctv.get("status", "")

    if avg_speed > 0:
        if avg_speed <= 20:
            score += 50
        elif avg_speed <= 40:
            score += 30
        elif avg_speed <= 60:
            score += 10

    if vehicle_count >= 15:
        score += 30
    elif vehicle_count >= 10:
        score += 15

    if "정체" in status:
        score += 30
    elif "주의" in status:
        score += 15

    return min(score, 100)


def get_risk_level(score):
    if score >= 70:
        return "높음"
    if score >= 40:
        return "주의"
    return "낮음"