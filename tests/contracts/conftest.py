import os
import uuid
from typing import Dict

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("GATEWAY_BASE_URL", "http://localhost:5000")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    client = httpx.Client(base_url=base_url, timeout=20.0)
    try:
        resp = client.get("/health")
        if resp.status_code >= 500:
            pytest.skip(f"Gateway healthcheck not ready: {resp.status_code}")
    except Exception:
        pytest.skip("api-gateway not reachable for contract tests")
    yield client
    client.close()


@pytest.fixture(scope="session")
def registered_user(client: httpx.Client) -> Dict[str, str]:
    email = f"contract-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Contract Tester",
        "email": email,
        "password": "Password123!",
        "tenant_name": f"tenant-{uuid.uuid4().hex[:8]}",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    return {
        "email": email,
        "password": payload["password"],
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "tenant_id": data.get("user", {}).get("tenant_id"),
    }


@pytest.fixture()
def auth_headers(registered_user: Dict[str, str]):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}
