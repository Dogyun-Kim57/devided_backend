from app.extensions import db
from app.models.post import Post


def save(post):
    db.session.add(post)
    db.session.commit()
    return post


def find_all():
    return Post.query.order_by(Post.created_at.desc()).all()


def find_by_id(post_id):
    return Post.query.get(post_id)