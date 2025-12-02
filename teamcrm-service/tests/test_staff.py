import os

import pytest

from flask_jwt_extended import create_access_token


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app

    application = create_app()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def auth_headers(app, identity: dict):
    with app.app_context():
        token = create_access_token(identity=str(identity.get('sub', '1')), additional_claims={'tenant_id': identity.get('tenant_id'), 'role': identity.get('role')})
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "teamcrm-service"


def test_create_staff(client):
    headers = auth_headers(client.application, {"tenant_id": 1, "role": "owner"})
    resp = client.post("/staff/", json={"name": "Joao"}, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert isinstance(data.get("id"), int)
