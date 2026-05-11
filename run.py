from app import create_app
from app.extensions import db, socketio

import app.models

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    socketio.run(
        app,
        host="127.0.0.1",
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True,
        use_reloader=False
    )