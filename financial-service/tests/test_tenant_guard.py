from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from app.tenant_guard import tenant_guard
from app.models import db


def build_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    JWTManager(app)
    db.init_app(app)

    @app.post("/tenants/<int:tenant_id>/receivables")
    @tenant_guard()
    def create_receivable(tenant_id):  # pragma: no cover
        return jsonify({"tenant_id": tenant_id})

    return app


def test_guard_rejects_mismatch():
    app = build_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 1})

    resp = client.post(
        "/tenants/2/receivables",
        json={"tenant_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_guard_accepts_match():
    app = build_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 3})

    resp = client.post(
        "/tenants/3/receivables",
        json={"tenant_id": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["tenant_id"] == 3
