from flask import Blueprint, request

from app.common.response import success, fail
from app.services.post_service import create_post, get_posts
from app.repositories.post_repository import find_by_id
from app.services.board_ai_service import analyze_image_file, summarize_pdf_file

board_api_bp = Blueprint("board_api", __name__)


@board_api_bp.route("/board/posts", methods=["GET"])
def board_posts():
    posts = get_posts()
    return success(posts)


@board_api_bp.route("/board/create", methods=["POST"])
def board_create():
    title = request.form.get("title")
    content = request.form.get("content")
    files = request.files.getlist("files")

    if not title or not content:
        return fail("title과 content가 필요합니다.", 400)

    post = create_post(title, content, files)

    return success(post, "게시글이 등록되었습니다.")


@board_api_bp.route("/board/file/analyze", methods=["POST"])
def analyze_board_file():
    data = request.get_json() or {}

    post_id = data.get("post_id")
    file_id = data.get("file_id")
    analysis_type = data.get("analysis_type")

    if not post_id or not file_id:
        return fail("post_id와 file_id가 필요합니다.", 400)

    post = find_by_id(post_id)

    if not post:
        return fail("게시글을 찾을 수 없습니다.", 404)

    target_file = None

    for file in post.files:
        if file.id == int(file_id):
            target_file = file
            break

    if not target_file:
        return fail("첨부파일을 찾을 수 없습니다.", 404)

    try:
        if analysis_type == "image":
            result = analyze_image_file(target_file.file_path)
        elif analysis_type == "pdf":
            result = summarize_pdf_file(target_file.file_path)
        else:
            return fail("지원하지 않는 분석 유형입니다.", 400)

        return success({
            "result": result
        })

    except Exception as e:
        print("[BOARD AI ANALYSIS ERROR]", e)
        return fail("AI 분석 중 오류가 발생했습니다.", 500)