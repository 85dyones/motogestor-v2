import os

import pytest

from flask_jwt_extended import create_access_token


@pytest.fixture()
def app(monkeypatch):
    # Set test DB to sqlite memory
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from app import create_app

    application = create_app()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def auth_headers(app, identity: dict):
    # create token inside app context so JWTManager is available
    with app.app_context():
        token = create_access_token(identity=identity)
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "management-service"


def test_create_and_get_customer(client):
    # create token with tenant_id and owner role
    headers = auth_headers(app, {"tenant_id": 1, "role": "owner"})

    # create customer
    resp = client.post("/customers/", json={"name": "Cliente Teste"}, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Cliente Teste" or data.get("name") == "Cliente Teste"

    customer_id = data.get("id")
    # get customer
    get_resp = client.get(f"/customers/{customer_id}", headers=headers)
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["name"] == "Cliente Teste"
