from __future__ import annotations

from app.identity import TENANT_ID_CLAIM
from app.models import RevokedToken, db
from flask_jwt_extended import decode_token

from .factories import create_tenant, create_user


def test_login_success(client):
    tenant = create_tenant()
    user = create_user(tenant, password="secret123")

    resp = client.post(
        "/auth/login",
        json={"email": user.email, "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    token = data["access_token"]
    assert data["refresh_token"]
    decoded = decode_token(token)
    assert int(decoded["sub"]) == user.id
    assert decoded[TENANT_ID_CLAIM] == tenant.id


def test_login_invalid_credentials(client):
    tenant = create_tenant()
    create_user(tenant, password="secret123")

    resp = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "bad"},
    )
    assert resp.status_code == 422


def test_me_respects_tenant_scope(client):
    tenant_a = create_tenant(name="A")
    user_a = create_user(tenant_a, password="secret123")
    tenant_b = create_tenant(name="B")
    create_user(tenant_b, password="secret123")

    login = client.post(
        "/auth/login",
        json={"email": user_a.email, "password": "secret123"},
    ).get_json()
    token = login["access_token"]

    # forcibly request user B by id but with token of A
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["tenant_id"] == tenant_a.id


def test_refresh_and_blocklist_flow(client):
    tenant = create_tenant(name="Refresh")
    user = create_user(tenant, password="secret123")

    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "secret123"},
    ).get_json()

    refresh_token = login["refresh_token"]
    refresh_resp = client.post(
        "/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert refresh_resp.status_code == 200
    new_access = refresh_resp.get_json()["access_token"]

    # logout current access token
    logout = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert logout.status_code == 200

    # token should now be blocked
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 401


def test_logout_all_inserts_blocklist_entries(client):
    tenant = create_tenant(name="Bulk")
    user = create_user(tenant, password="secret123")

    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "secret123"},
    ).get_json()
    access_token = login["access_token"]

    resp = client.post(
        "/auth/logout_all", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200

    assert db.session.query(RevokedToken).count() >= 3
