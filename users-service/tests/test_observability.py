def test_trace_id_header_propagated(client):
    resp = client.get("/health", headers={"X-Trace-Id": "abc123"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Trace-Id") == "abc123"


def test_metrics_endpoint_available(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"http_requests_total" in resp.data
