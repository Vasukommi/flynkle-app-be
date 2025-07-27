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

@pytest.fixture
def client():
    engine = create_engine("sqlite:///./test_conv.db", connect_args={"check_same_thread": False})
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
    os.remove("test_conv.db")


def create_token(client):
    data = {"provider": "email", "email": "conv@example.com", "password": "pwd"}
    client.post("/api/v1/users", json=data)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "conv@example.com", "password": "pwd"},
    )
    return resp.json()["data"]["access_token"]


def test_plan_enforcement(client):
    token = create_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    for i in range(20):
        resp = client.post(
            f"/api/v1/conversations/{conv['conversation_id']}/messages",
            headers=headers,
            json={"content": {"t": i}, "message_type": "user"},
        )
        assert resp.status_code == 200
    # 21st message should fail
    resp = client.post(
        f"/api/v1/conversations/{conv['conversation_id']}/messages",
        headers=headers,
        json={"content": {"t": 21}, "message_type": "user"},
    )
    assert resp.status_code == 403
    assert resp.json()["message"] == "Upgrade required"


def test_update_message(client):
    user_id = create_user(client)
    headers = {"X-User-ID": user_id}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    msg = client.post(
        f"/api/v1/conversations/{conv['conversation_id']}/messages",
        headers=headers,
        json={"content": {"t": 1}, "message_type": "user"},
    ).json()["data"]
    updated = client.patch(
        f"/api/v1/messages/{msg['message_id']}",
        headers=headers,
        json={"content": {"t": 2}, "extra": {"edited": True}},
    )
    assert updated.status_code == 200
    data = updated.json()["data"]
    assert data["content"] == {"t": 2}
    assert data["extra"] == {"edited": True}
