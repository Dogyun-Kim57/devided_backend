import os
from pathlib import Path
from typing import TypedDict, Literal
from datetime import datetime, timedelta

import requests
from flask import current_app

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, END

VECTOR_DIR = "app/vectorstores/board_pdf"

CONVERSATION_MEMORY = []


class AssistantState(TypedDict):
    question: str
    mode: str
    context: str
    answer: str


def get_current_time_text():
    utc_now = datetime.utcnow()
    korea_now = utc_now + timedelta(hours=9)

    return korea_now.strftime("%Y년 %m월 %d일 %H시 %M분")


def get_llm():
    return ChatOpenAI(
        api_key=current_app.config.get("LLM_API_KEY"),
        model=current_app.config.get("LLM_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )


def get_embeddings():
    return OpenAIEmbeddings(
        api_key=current_app.config.get("LLM_API_KEY"),
        model="text-embedding-3-small",
    )


def save_to_memory(role: str, content: str):
    CONVERSATION_MEMORY.append({
        "role": role,
        "content": content
    })

    if len(CONVERSATION_MEMORY) > 12:
        CONVERSATION_MEMORY.pop(0)


def get_memory_text():
    if not CONVERSATION_MEMORY:
        return "아직 저장된 이전 대화가 없습니다."

    lines = []

    for item in CONVERSATION_MEMORY:
        if item["role"] == "user":
            lines.append(f"사용자: {item['content']}")
        else:
            lines.append(f"AI: {item['content']}")

    return "\n".join(lines)


def resolve_static_file_path(file_path: str) -> Path:
    cleaned_path = file_path.lstrip("/")

    if cleaned_path.startswith("static/"):
        return Path("app") / cleaned_path

    return Path(cleaned_path)


def build_pdf_vectorstore(file_path: str):
    path = resolve_static_file_path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {path}")

    loader = PyPDFLoader(str(path))
    docs = loader.load()

    if not docs:
        raise ValueError("PDF에서 텍스트를 추출하지 못했습니다.")

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)

    os.makedirs(VECTOR_DIR, exist_ok=True)
    vectorstore.save_local(VECTOR_DIR)

    return {
        "message": "PDF 벡터스토어 생성 완료",
        "pages": len(docs),
        "vector_dir": VECTOR_DIR,
    }


def load_retriever():
    embeddings = get_embeddings()

    vectorstore = FAISS.load_local(
        VECTOR_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    return vectorstore.as_retriever(search_kwargs={"k": 3})


def fetch_current_weather(city: str = None):
    api_key = current_app.config.get("WEATHER_API_KEY")
    default_city = current_app.config.get("DEFAULT_WEATHER_CITY", "Seoul")
    target_city = city or default_city

    if not api_key:
        raise RuntimeError("WEATHER_API_KEY가 설정되어 있지 않습니다.")

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": target_city,
        "appid": api_key,
        "units": "metric",
        "lang": "kr",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    weather = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    clouds = data.get("clouds", {})

    return {
        "city": data.get("name", target_city),
        "description": weather.get("description", "-"),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),
        "cloudiness": clouds.get("all"),
    }


def extract_city_from_question(question: str):
    city_map = {
        "서울": "Seoul",
        "인천": "Incheon",
        "경기": "Suwon",
        "수원": "Suwon",
        "대전": "Daejeon",
        "대구": "Daegu",
        "광주": "Gwangju",
        "부산": "Busan",
        "울산": "Ulsan",
        "제주": "Jeju",
    }

    for korean_name, english_name in city_map.items():
        if korean_name in question:
            return english_name

    return current_app.config.get("DEFAULT_WEATHER_CITY", "Seoul")


def answer_with_weather_chain(question: str):
    memory_text = get_memory_text()
    current_time = get_current_time_text()

    city = extract_city_from_question(question)
    weather = fetch_current_weather(city)

    weather_text = f"""
도시: {weather["city"]}
날씨: {weather["description"]}
기온: {weather["temperature"]}℃
체감온도: {weather["feels_like"]}℃
습도: {weather["humidity"]}%
기압: {weather["pressure"]} hPa
풍속: {weather["wind_speed"]} m/s
구름량: {weather["cloudiness"]}%
"""

    prompt = ChatPromptTemplate.from_template("""
너는 AI 교통 관제 시스템의 기상 분석 보조 AI다.

[현재 서버 시간]
{current_time}

[이전 대화]
{memory}

[현재 날씨 데이터]
{weather_text}

[질문]
{question}

[답변 형식]
1. 현재 날씨 요약
2. 교통 관제 관점의 위험 요소
3. 현재 프로젝트와 연결 가능한 포인트
""")

    chain = prompt | get_llm()

    response = chain.invoke({
        "current_time": current_time,
        "memory": memory_text,
        "weather_text": weather_text,
        "question": question,
    })

    return response.content


def answer_with_rag(question: str):
    memory_text = get_memory_text()
    current_time = get_current_time_text()

    retriever = load_retriever()
    related_docs = retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in related_docs
    )

    prompt = ChatPromptTemplate.from_template("""
너는 AI 교통 관제 프로젝트의 RAG 보조 AI다.

문서에 없는 내용은 단정하지 말고
"문서 기준으로는 확인되지 않습니다"라고 말해라.

[현재 서버 시간]
{current_time}

[이전 대화]
{memory}

[검색된 문서 내용]
{context}

[질문]
{question}

[답변 형식]
1. 문서 기반 답변
2. 현재 AI 교통 관제 프로젝트와의 연결점
3. 발표에 사용할 수 있는 문장
""")

    chain = prompt | get_llm()

    response = chain.invoke({
        "current_time": current_time,
        "memory": memory_text,
        "context": context,
        "question": question,
    })

    return response.content


def answer_with_basic_chain(question: str):
    memory_text = get_memory_text()
    current_time = get_current_time_text()

    prompt = ChatPromptTemplate.from_template("""
너는 AI 교통 관제 시스템의 보조 AI다.

[현재 서버 시간]
{current_time}

[이전 대화]
{memory}

[현재 질문]
{question}

답변 규칙:
- 한국어로 답변한다.
- 현재 시간이나 날짜 질문은 현재 서버 시간 기준으로 답한다.
- CCTV, YOLO, WebSocket, 탐지 레포트, 대보정보통신 요구사항과 연결 가능하면 연결한다.
- 확실하지 않은 내용은 단정하지 않는다.
""")

    chain = prompt | get_llm()

    response = chain.invoke({
        "current_time": current_time,
        "memory": memory_text,
        "question": question,
    })

    return response.content


def answer_with_search_chain(question: str):
    memory_text = get_memory_text()
    current_time = get_current_time_text()

    search = DuckDuckGoSearchRun()
    search_result = search.invoke(question)

    prompt = ChatPromptTemplate.from_template("""
너는 AI 교통 관제 시스템의 검색 보조 AI다.

최신 정보는 검색 결과 기준으로만 말하고,
불확실하면 확인 필요라고 표시해라.

[현재 서버 시간]
{current_time}

[이전 대화]
{memory}

[검색 결과]
{search_result}

[질문]
{question}

[답변 형식]
1. 검색 결과 요약
2. 교통/관제 관점의 의미
3. 현재 프로젝트와 연결 가능한 포인트
""")

    chain = prompt | get_llm()

    response = chain.invoke({
        "current_time": current_time,
        "memory": memory_text,
        "search_result": search_result,
        "question": question,
    })

    return response.content


def classify_question(question: str) -> Literal["rag", "search", "weather", "basic"]:
    q = question.lower()

    if any(keyword in q for keyword in [
        "날씨", "기온", "비", "눈", "강수", "우천", "안개", "풍속", "기상"
    ]):
        return "weather"

    if any(keyword in q for keyword in [
        "pdf", "문서", "자료", "리트리버", "retriever", "rag", "업로드"
    ]):
        return "rag"

    if any(keyword in q for keyword in [
        "최신", "검색", "인터넷", "뉴스", "오늘"
    ]):
        return "search"

    return "basic"


def router_node(state: AssistantState):
    mode = classify_question(state["question"])

    return {
        **state,
        "mode": mode,
    }


def basic_node(state: AssistantState):
    answer = answer_with_basic_chain(state["question"])

    return {
        **state,
        "answer": answer,
    }


def rag_node(state: AssistantState):
    answer = answer_with_rag(state["question"])

    return {
        **state,
        "answer": answer,
    }


def search_node(state: AssistantState):
    answer = answer_with_search_chain(state["question"])

    return {
        **state,
        "answer": answer,
    }


def weather_node(state: AssistantState):
    answer = answer_with_weather_chain(state["question"])

    return {
        **state,
        "answer": answer,
    }


def route_by_mode(state: AssistantState):
    if state["mode"] == "weather":
        return "weather"

    if state["mode"] == "rag":
        return "rag"

    if state["mode"] == "search":
        return "search"

    return "basic"


def run_langgraph_assistant(question: str):
    save_to_memory("user", question)

    graph = StateGraph(AssistantState)

    graph.add_node("router", router_node)
    graph.add_node("basic", basic_node)
    graph.add_node("rag", rag_node)
    graph.add_node("search", search_node)
    graph.add_node("weather", weather_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_by_mode,
        {
            "basic": "basic",
            "rag": "rag",
            "search": "search",
            "weather": "weather",
        }
    )

    graph.add_edge("basic", END)
    graph.add_edge("rag", END)
    graph.add_edge("search", END)
    graph.add_edge("weather", END)

    app = graph.compile()

    result = app.invoke({
        "question": question,
        "mode": "",
        "context": "",
        "answer": "",
    })

    answer = result["answer"]
    mode = result["mode"]

    save_to_memory("assistant", answer)

    return answer, mode