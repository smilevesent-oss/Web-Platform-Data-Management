"""Tests run against a real PostgreSQL database.

Set TEST_DATABASE_URL (default: postgresql+psycopg://docrepo:docrepo@localhost:5432/docrepo_test).
The database is wiped and re-seeded at the start of the test session.
"""
import os

import pytest

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://docrepo:docrepo@localhost:5432/docrepo_test"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from seed.seed import DEMO_PASSWORD, run  # noqa: E402


@pytest.fixture(scope="session")
def client():
    run(reset=True)
    with TestClient(app) as c:
        yield c


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def auth(client):
    cache = {}

    def get(username):
        if username not in cache:
            cache[username] = _login(client, username)
        return cache[username]

    return get
