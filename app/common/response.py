from flask import jsonify


def success(data=None, message="success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    })


def fail(message="error", status_code=400):
    return jsonify({
        "success": False,
        "message": message,
        "data": None
    }), status_code