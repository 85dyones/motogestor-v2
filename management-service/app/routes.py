from flask import Blueprint, jsonify

bp = Blueprint("management", __name__)

@bp.get("/")
def index():
    return jsonify({"message": "management-service ok"})
