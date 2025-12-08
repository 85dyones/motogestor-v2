import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import httpx
import pytest


def _bootstrap_stack_if_requested() -> bool:
    if os.getenv("AUTO_START_STACK") != "1":
        return False

    script_path = Path(__file__).resolve().parents[1] / "start_stack.sh"
    env = os.environ.copy()
    env.setdefault("LEAVE_UP", "1")
    env.setdefault("COMPOSE_FILE", env.get("COMPOSE_FILE", "docker-compose.test.yml"))
    env.setdefault("ENV_FILE", env.get("ENV_FILE", ".env.test"))
    env.setdefault("GATEWAY_PORT", env.get("GATEWAY_PORT", "5000"))
    try:
        subprocess.run([str(script_path)], env=env, check=True)
    except FileNotFoundError:
        pytest.skip("docker not installed; cannot bootstrap contract stack")
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"failed to bootstrap stack: {exc}")
    return True


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("GATEWAY_BASE_URL", "http://localhost:5000")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    started = False
    client = httpx.Client(base_url=base_url, timeout=20.0)
    try:
        try:
            resp = client.get("/health")
            if resp.status_code >= 500:
                raise RuntimeError(f"Gateway unhealthy: {resp.status_code}")
        except Exception:
            started = _bootstrap_stack_if_requested()
            if started:
                resp = client.get("/health")
                if resp.status_code >= 500:
                    raise RuntimeError(f"Gateway unhealthy after bootstrap: {resp.status_code}")
            else:
                pytest.skip("api-gateway not reachable for contract tests")
        yield client
    finally:
        client.close()
        if started:
            teardown_env = os.environ.copy()
            teardown_env.update({"TEARDOWN": "1", "LEAVE_UP": "0"})
            script_path = Path(__file__).resolve().parents[1] / "start_stack.sh"
            subprocess.run([str(script_path)], env=teardown_env, check=False)


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
