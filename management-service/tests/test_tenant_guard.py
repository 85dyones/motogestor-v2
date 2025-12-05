from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from app.tenant_guard import tenant_guard
from app.models import db


def _app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    JWTManager(app)
    db.init_app(app)

    @app.post("/t/<int:tenant_id>")
    @tenant_guard()
    def handler(tenant_id):  # pragma: no cover
        return jsonify({"tenant_id": tenant_id})

    return app


def test_tenant_guard_allows_path_only():
    app = _app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 5})

    resp = client.post("/t/5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_tenant_guard_rejects_mismatch():
    app = _app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 5})

    resp = client.post(
        "/t/7", json={"tenant_id": 7}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_tenant_guard_passes_on_match():
    app = _app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 7})

    resp = client.post(
        "/t/7", json={"tenant_id": 7}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
