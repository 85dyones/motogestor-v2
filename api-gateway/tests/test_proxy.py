import json

from flask import Flask

import pytest


def test_filter_request_headers(monkeypatch):
    from app.proxy import _filter_request_headers

    app = Flask("test")

    headers = {
        "Host": "example.com",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "X-Custom": "value",
    }

    with app.test_request_context("/some", headers=headers):
        out = _filter_request_headers()

    # Host and Connection should be excluded
    assert "Connection" not in out
    assert "Host" not in out
    assert out.get("Content-Type") == "application/json"
    assert out.get("X-Custom") == "value"


class DummyResp:
    def __init__(self, status_code=200, headers=None, content=b"ok"):
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self.content = content


def test_forward_request_makes_http_call(monkeypatch):
    from app.proxy import forward_request
    from flask import request

    # Prepare a Flask app context with a fake request
    app = Flask("test")

    def fake_request(method, url, headers, params, data, cookies, timeout):
        # validate inputs
        assert method == "POST"
        assert url.endswith("/path/1")
        return DummyResp(status_code=201, headers={"X-Ok": "1"}, content=b"created")

    monkeypatch.setattr("requests.request", fake_request)

    with app.test_request_context("/proxy", method="POST", data=json.dumps({"a": 1}), headers={"X-Trace": "1"}):
        resp = forward_request("http://upstream-service:5000", "path/1")

    assert resp.status_code == 201
    assert resp.get_data() == b"created"
    assert resp.headers.get("X-Ok") == "1"
