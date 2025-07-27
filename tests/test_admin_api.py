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
    engine = create_engine("sqlite:///./test_admin.db", connect_args={"check_same_thread": False})
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
    os.remove("test_admin.db")


def create_user_and_login(client, email, is_admin=False):
    data = {"provider": "email", "email": email, "password": "pwd"}
    if is_admin:
        data["is_admin"] = True
    resp = client.post("/api/v1/users", json=data)
    user_id = resp.json()["data"]["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "pwd"})
    token = login.json()["data"]["access_token"]
    return user_id, token


def test_admin_required(client):
    _, token = create_user_and_login(client, "user@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["message"] == "Admin privileges required"


def test_admin_can_access(client):
    _, token = create_user_and_login(client, "admin@example.com", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["code"] == 200


def test_admin_create_and_delete_user(client):
    _, token = create_user_and_login(client, "admin2@example.com", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    new_user = {"provider": "email", "email": "new@example.com", "password": "pwd"}
    create_resp = client.post("/api/v1/admin/users", headers=headers, json=new_user)
    assert create_resp.status_code == 200
    uid = create_resp.json()["data"]["user_id"]

    delete_resp = client.delete(f"/api/v1/admin/users/{uid}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["user_id"] == uid


def test_admin_requires_jwt_header(client):
    admin_id, _ = create_user_and_login(client, "tokenless@example.com", is_admin=True)
    resp = client.get("/api/v1/admin/users", headers={"X-User-ID": admin_id})
    assert resp.status_code == 401


def test_suspend_and_reinstate_user(client):
    user_id, _ = create_user_and_login(client, "target@example.com")
    _, token = create_user_and_login(client, "boss@example.com", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}
    suspend = client.post(f"/api/v1/admin/users/{user_id}/suspend", headers=headers)
    assert suspend.status_code == 200
    assert suspend.json()["data"]["is_suspended"] is True
    reinstate = client.post(
        f"/api/v1/admin/users/{user_id}/reinstate", headers=headers
    )
    assert reinstate.status_code == 200
    assert reinstate.json()["data"]["is_suspended"] is False


def test_admin_view_conversations_and_usage(client):
    user_id, token = create_user_and_login(client, "convuser@example.com")
    _, admin_token = create_user_and_login(
        client, "watcher@example.com", is_admin=True
    )
    user_headers = {"Authorization": f"Bearer {token}"}
    conv = client.post("/api/v1/conversations", headers=user_headers, json={}).json()[
        "data"
    ]
    client.post(
        f"/api/v1/conversations/{conv['conversation_id']}/messages",
        headers=user_headers,
        json={"content": {"t": 1}, "message_type": "user"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    convs = client.get(
        f"/api/v1/admin/users/{user_id}/conversations", headers=admin_headers
    )
    assert convs.status_code == 200
    assert len(convs.json()["data"]) == 1
    usage = client.get(f"/api/v1/admin/users/{user_id}/usage", headers=admin_headers)
    assert usage.status_code == 200
    assert len(usage.json()["data"]) >= 1
