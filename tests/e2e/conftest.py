import os
import time
import uuid
from typing import Dict, Tuple

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("GATEWAY_BASE_URL", "http://localhost:5000").rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    client = httpx.Client(base_url=base_url, timeout=30.0)
    for _ in range(30):
        try:
            resp = client.get("/health")
            if resp.status_code < 500:
                break
        except Exception:
            time.sleep(2)
            continue
    else:
        pytest.skip("api-gateway not reachable for e2e tests")
    yield client
    client.close()


@pytest.fixture(scope="session")
def seed_user(client: httpx.Client) -> Tuple[Dict[str, str], str]:
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    tenant_name = f"tenant-{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/auth/register",
        json={
            "name": "E2E Owner",
            "email": email,
            "password": password,
            "tenant_name": tenant_name,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    payload = resp.json()
    access_token = payload["access_token"]
    tenant_id = payload["user"]["tenant_id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers, tenant_id
