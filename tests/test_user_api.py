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
    engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
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
    os.remove("test.db")


def test_create_duplicate_user(client):
    data = {"provider": "email", "email": "dup@example.com", "password": "pwd"}
    resp1 = client.post("/api/v1/users", json=data)
    assert resp1.status_code == 200
    resp2 = client.post("/api/v1/users", json=data)
    assert resp2.status_code == 400
    assert resp2.json()["message"] == "User already exists"


def test_user_has_default_plan(client):
    data = {"provider": "email", "email": "plan@example.com", "password": "pwd"}
    resp = client.post("/api/v1/users", json=data)
    assert resp.status_code == 200
    assert resp.json()["data"]["plan"] == "free"


def create_user_and_login(client, email="u@example.com", is_admin=False):
    data = {"provider": "email", "email": email, "password": "pwd"}
    if is_admin:
        data["is_admin"] = True
    resp = client.post("/api/v1/users", json=data)
    user_id = resp.json()["data"]["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "pwd"})
    token = login.json()["data"]["access_token"]
    return user_id, token


def test_list_users_requires_auth(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401


def test_get_user_requires_auth(client):
    user_id = client.post(
        "/api/v1/users",
        json={"provider": "email", "email": "nouser@example.com", "password": "pwd"},
    ).json()["data"]["user_id"]
    resp = client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 401


def test_non_admin_access_forbidden(client):
    uid1, token1 = create_user_and_login(client, "normal1@example.com")
    uid2, _ = create_user_and_login(client, "normal2@example.com")
    headers = {"Authorization": f"Bearer {token1}"}
    resp = client.get(f"/api/v1/users/{uid2}", headers=headers)
    assert resp.status_code == 403


def test_non_admin_cannot_list_users(client):
    _, token = create_user_and_login(client, "list@example.com")
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_create_user_validation(client):
    resp = client.post("/api/v1/users", json={"email": "bad"})
    assert resp.status_code == 422
