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
    engine = create_engine("sqlite:///./test_chat.db", connect_args={"check_same_thread": False})
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
    os.remove("test_chat.db")


def create_user_and_login(client):
    client.post("/api/v1/users", json={"provider": "email", "email": "chat@example.com", "password": "pwd"})
    resp = client.post("/api/v1/auth/login", json={"email": "chat@example.com", "password": "pwd"})
    return resp.json()["data"]["access_token"]


def test_chat_with_memory(client, monkeypatch):
    token = create_user_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.api.v1.endpoints.chat as chat_ep
    monkeypatch.setattr(chat_ep, "check_chat_rate_limit", lambda _u: None)
    monkeypatch.setattr(chat_ep, "chat_with_openai_history", lambda m: ("hi", 2))
    resp = client.post("/api/v1/chat", headers=headers, json={"message": "hello", "conversation_id": conv["conversation_id"]})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["response"] == "hi"
    msgs = client.get(f"/api/v1/conversations/{conv['conversation_id']}/messages", headers=headers).json()["data"]
    assert len(msgs) == 2


def test_chat_openai_failure(client, monkeypatch):
    token = create_user_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.api.v1.endpoints.chat as chat_ep
    def fail(_):
        raise RuntimeError("boom")
    monkeypatch.setattr(chat_ep, "chat_with_openai_history", fail)
    resp = client.post("/api/v1/chat", headers=headers, json={"message": "hello", "conversation_id": conv["conversation_id"]})
    assert resp.status_code == 502
    assert resp.json()["data"]["source"] == "openai"


def test_chat_token_quota(client, monkeypatch):
    token = create_user_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.core.plans as plans
    plans.PLANS["free"]["daily_tokens"] = 2
    import app.api.v1.endpoints.chat as chat_ep
    monkeypatch.setattr(chat_ep, "check_chat_rate_limit", lambda _u: None)
    monkeypatch.setattr(chat_ep, "chat_with_openai_history", lambda m: ("ok", 1))
    for _ in range(2):
        resp = client.post("/api/v1/chat", headers=headers, json={"message": "hello", "conversation_id": conv["conversation_id"]})
        assert resp.status_code == 200
    resp = client.post("/api/v1/chat", headers=headers, json={"message": "again", "conversation_id": conv["conversation_id"]})
    assert resp.status_code == 403
