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
