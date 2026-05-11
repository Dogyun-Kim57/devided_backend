from flask import current_app

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def ask_traffic_assistant(user_message):
    api_key = current_app.config.get("LLM_API_KEY")
    model = current_app.config.get("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        return "LLM_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요."

    if OpenAI is None:
        return "openai 패키지가 설치되어 있지 않습니다."

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            instructions="""
너는 AI 교통 관제 시스템의 보조 AI다.

답변 규칙:
- 한국어로 답변한다.
- 너무 길게 설명하지 않는다.
- CCTV, YOLO, WebSocket, 탐지 레포트, 교통 관제 흐름과 연결해서 설명한다.
- 확실하지 않은 내용은 확인 필요라고 말한다.
""",
            input=user_message,
        )

        return response.output_text

    except Exception as e:
        print("[ASSISTANT ERROR]", e)
        return "AI 응답 생성 중 오류가 발생했습니다."