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
from app.repositories import user as user_repo
from app.schemas.user import UserCreate


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///./test_conv.db", connect_args={"check_same_thread": False}
    )
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


def create_user(client):
    data = {"provider": "email", "email": "convuser@example.com", "password": "pwd"}
    resp = client.post("/api/v1/users", json=data)
    return resp.json()["data"]["user_id"]


def test_plan_enforcement(client):
    token = create_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.api.v1.endpoints.conversations as conv_ep

    original = conv_ep.check_message_rate_limit
    conv_ep.check_message_rate_limit = lambda _u: None
    try:
        for i in range(20):
            resp = client.post(
                f"/api/v1/conversations/{conv['conversation_id']}/messages",
                headers=headers,
                json={"content": {"t": i}, "message_type": "user"},
            )
            assert resp.status_code == 200
    finally:
        conv_ep.check_message_rate_limit = original
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


def test_conversation_limit(client):
    token = create_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(3):
        resp = client.post("/api/v1/conversations", headers=headers, json={})
        assert resp.status_code == 200
    resp = client.post("/api/v1/conversations", headers=headers, json={})
    assert resp.status_code == 403
    assert resp.json()["message"] == "Upgrade required"


def test_token_limit_enforced(client, monkeypatch):
    token = create_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.core.plans as plans

    plans.PLANS["free"]["daily_tokens"] = 2
    import app.api.v1.endpoints.conversations as conv_ep

    monkeypatch.setattr(conv_ep, "chat_with_openai", lambda m: ("ok", 1))
    orig_rate = conv_ep.check_message_rate_limit
    conv_ep.check_message_rate_limit = lambda _u: None
    try:
        for _ in range(2):
            resp = client.post(
                f"/api/v1/conversations/{conv['conversation_id']}/messages",
                headers=headers,
                json={"content": {"t": 1}, "message_type": "user", "invoke_llm": True},
            )
            assert resp.status_code == 200
        resp = client.post(
            f"/api/v1/conversations/{conv['conversation_id']}/messages",
            headers=headers,
            json={"content": {"t": 1}, "message_type": "user", "invoke_llm": True},
        )
        assert resp.status_code == 403
    finally:
        conv_ep.check_message_rate_limit = orig_rate


def test_downgrade_blocked_when_over_quota(client):
    token = create_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/v1/user/upgrade", params={"plan": "pro"}, headers=headers)
    assert resp.status_code == 200
    for _ in range(4):
        client.post("/api/v1/conversations", headers=headers, json={})
    resp = client.post("/api/v1/user/upgrade", params={"plan": "free"}, headers=headers)
    assert resp.status_code == 400


def create_auth(client):
    uid = create_user(client)
    token = client.post(
        "/api/v1/auth/login", json={"email": "convuser@example.com", "password": "pwd"}
    ).json()["data"]["access_token"]
    return uid, {"Authorization": f"Bearer {token}"}


def test_conversation_crud(client):
    uid, headers = create_auth(client)
    conv = client.post(
        "/api/v1/conversations", headers=headers, json={"title": "A"}
    ).json()["data"]
    conv_id = conv["conversation_id"]
    assert (
        client.get(f"/api/v1/conversations/{conv_id}", headers=headers).status_code
        == 200
    )
    upd = client.patch(
        f"/api/v1/conversations/{conv_id}", headers=headers, json={"title": "B"}
    )
    assert upd.status_code == 200
    assert upd.json()["data"]["title"] == "B"
    assert (
        client.delete(f"/api/v1/conversations/{conv_id}", headers=headers).status_code
        == 200
    )
    assert (
        client.get(f"/api/v1/conversations/{conv_id}", headers=headers).status_code
        == 404
    )


def test_message_crud(client):
    _, headers = create_auth(client)
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    msg = client.post(
        f"/api/v1/conversations/{conv['conversation_id']}/messages",
        headers=headers,
        json={"content": {"a": 1}, "message_type": "user"},
    ).json()["data"]
    mid = msg["message_id"]
    assert client.get(f"/api/v1/messages/{mid}", headers=headers).status_code == 200
    assert (
        client.patch(
            f"/api/v1/messages/{mid}", headers=headers, json={"content": {"a": 2}}
        ).status_code
        == 200
    )
    assert client.delete(f"/api/v1/messages/{mid}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/messages/{mid}", headers=headers).status_code == 404


def test_search_and_bulk_delete(client):
    _, headers = create_auth(client)
    ids = []
    for i in range(3):
        resp = client.post(
            "/api/v1/conversations", headers=headers, json={"title": f"Topic {i}"}
        )
        ids.append(resp.json()["data"]["conversation_id"])
    resp = client.get("/api/v1/conversations", headers=headers, params={"q": "Topic 1"})
    assert len(resp.json()["data"]) == 1
    del_resp = client.delete(
        "/api/v1/conversations", headers=headers, params=[("ids", i) for i in ids]
    )
    assert del_resp.status_code == 200
    assert client.get("/api/v1/conversations", headers=headers).json()["data"] == []


def test_file_upload_and_message(client, monkeypatch):
    _, headers = create_auth(client)
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()["data"]
    import app.api.v1.endpoints.uploads as upload_ep

    monkeypatch.setattr(upload_ep, "upload_file_obj", lambda f: ("test.txt", 1))
    monkeypatch.setattr(upload_ep, "get_file_url", lambda k: f"http://minio/{k}")
    import app.core.plans as plans

    plans.PLANS["free"]["max_file_uploads"] = 1
    upload = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("t.txt", b"x", "text/plain")},
    )
    url = upload.json()["data"]["url"]
    second = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("t2.txt", b"y", "text/plain")},
    )
    assert second.status_code == 403
    msg_resp = client.post(
        f"/api/v1/conversations/{conv['conversation_id']}/messages",
        headers=headers,
        json={"content": {"url": url, "name": "t.txt"}, "message_type": "file"},
    )
    assert msg_resp.status_code == 200
