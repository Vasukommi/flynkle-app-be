import os
import sys

os.environ.setdefault("OPENAI_API_KEY", "test")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.core import decode_access_token


@pytest.fixture
def client():
    engine = create_engine("sqlite:///./test_misc.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    os.remove("test_misc.db")


def create_user_and_login(client, email="user@example.com"):
    client.post("/api/v1/users", json={"provider": "email", "email": email, "password": "pwd"})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "pwd"})
    return resp.json()["data"]["access_token"]


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"


def test_last_login_set(client):
    token = create_user_and_login(client, "login@example.com")
    user_id = decode_access_token(token)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["last_login"] is not None


def test_message_rate_limit(client):
    token = create_user_and_login(client, "rate@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    url = f"/api/v1/conversations/{conv['conversation_id']}/messages"
    for _ in range(5):
        assert client.post(url, headers=headers, json={"content": {"t": 1}, "message_type": "user"}).status_code == 200
    resp = client.post(url, headers=headers, json={"content": {"t": 2}, "message_type": "user"})
    assert resp.status_code == 429
