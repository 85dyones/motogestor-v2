import json

from flask import Flask, jsonify


def test_auth_route_forwards(monkeypatch):
    from app.routes_auth import auth_proxy

    called = {}

    def fake_forward_request(base_url, subpath):
        called['base'] = base_url
        called['subpath'] = subpath
        # return a Flask response-like object
        app = Flask('test')
        with app.test_request_context():
            return jsonify({'ok': True}), 200

    monkeypatch.setattr('app.routes_auth.forward_request', fake_forward_request)

    app = Flask('test')
    app.register_blueprint(jsonify) if False else None

    with app.test_request_context('/auth/login'):
        resp = auth_proxy('login')

    assert called['subpath'].endswith('login')


def test_service_routes_forward(monkeypatch):
    from app.routes_services import management_proxy

    called = {}

    def fake_forward_request(base_url, path):
        called['base'] = base_url
        called['path'] = path
        app = Flask('test')
        with app.test_request_context():
            return jsonify({'ok': True}), 200

    monkeypatch.setattr('app.routes_services.forward_request', fake_forward_request)

    app = Flask('test')
    with app.test_request_context('/management/customers'):
        resp = management_proxy('customers')

    assert called['path'].startswith('customers')
