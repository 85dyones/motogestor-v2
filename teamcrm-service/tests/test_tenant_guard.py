from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from app.tenant_guard import tenant_guard
from app.models import db


def make_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    JWTManager(app)
    db.init_app(app)

    @app.post("/tenants/<int:tenant_id>/tasks")
    @tenant_guard()
    def create_task(tenant_id):  # pragma: no cover
        return jsonify({"tenant_id": tenant_id})

    return app


def test_guard_allows_path_only():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 9})

    resp = client.post("/tenants/9/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_guard_rejects_mismatch():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 9})

    resp = client.post(
        "/tenants/8/tasks",
        json={"tenant_id": 8},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_guard_accepts_match():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 3})

    resp = client.post(
        "/tenants/3/tasks",
        json={"tenant_id": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["tenant_id"] == 3
