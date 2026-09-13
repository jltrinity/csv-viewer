import io

import pytest
from flask import template_rendered

from app import app


@pytest.fixture
def cache(monkeypatch):
    isolated_cache = {}
    monkeypatch.setattr('app.CSV_CACHE', isolated_cache)
    return isolated_cache


@pytest.fixture(autouse=True)
def configure_app(monkeypatch, cache):
    monkeypatch.setitem(app.config, 'TESTING', True)
    monkeypatch.setitem(app.config, 'SECRET_KEY', 'test-secret')


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def context():
    captured = {}

    def capture(sender, template, context, **extra):
        captured.clear()
        captured.update(context)

    template_rendered.connect(capture, app)
    try:
        yield captured
    finally:
        template_rendered.disconnect(capture, app)


@pytest.fixture
def upload(client):
    default_client = client

    def send(content=b'temperatura,presion\n20,1012\n25,1010\n', filename='datos.csv', client=None):
        return (client or default_client).post('/', data={
            'action': 'load', 'csv_file': (io.BytesIO(content), filename),
        })

    return send
