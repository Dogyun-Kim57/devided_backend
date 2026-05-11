from app.extensions import db
from app.models.camera import Camera


def find_all():
    return Camera.query.order_by(Camera.id.asc()).all()


def count_all():
    return Camera.query.count()


def count_live():
    return Camera.query.filter_by(is_live=True).count()


def save(camera):
    db.session.add(camera)
    db.session.commit()
    return camera