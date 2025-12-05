from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from app.tenant_guard import tenant_guard
from app.models import db


def _make_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    JWTManager(app)
    db.init_app(app)

    @app.route("/tenants/<int:tenant_id>/resource", methods=["POST"])
    @tenant_guard()
    def guarded(tenant_id):  # pragma: no cover - behavior tested via client
        return jsonify({"tenant_id": tenant_id})

    return app


def test_tenant_guard_blocks_mismatch():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 10})

    resp = client.post(
        "/tenants/99/resource",
        json={"tenant_id": 99},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_tenant_guard_allows_match():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="1", additional_claims={"tenant_id": 7})

    resp = client.post(
        "/tenants/7/resource",
        json={"tenant_id": 7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["tenant_id"] == 7
