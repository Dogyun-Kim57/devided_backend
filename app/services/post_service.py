import os
from werkzeug.utils import secure_filename

from app.models.post import Post, PostFile
from app.repositories import post_repository

UPLOAD_DIR = "app/static/uploads/board"


def create_post(title, content, files):
    post = Post(title=title, content=content)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_DIR, filename)

            file.save(path)

            post.files.append(
                PostFile(
                    filename=filename,
                    file_path=f"/static/uploads/board/{filename}"
                )
            )

    saved = post_repository.save(post)
    return convert_post_to_dict(saved)


def get_posts():
    posts = post_repository.find_all()
    return [convert_post_to_dict(post) for post in posts]


def convert_post_to_dict(post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "file_path": file.file_path,
            }
            for file in post.files
        ]
    }