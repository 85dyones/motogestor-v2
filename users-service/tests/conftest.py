import os
import pytest

from app import create_app
from app.models import db


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    application = create_app()
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
