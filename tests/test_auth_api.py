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
from app.core import create_access_token
from app.core.security import decode_access_token

@pytest.fixture
def client():
    engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
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
    os.remove("test_auth.db")


def create_user(client, email="edge@example.com"):
    client.post("/api/v1/users", json={"provider": "email", "email": email, "password": "pwd"})


def login(client, email="edge@example.com", password="pwd"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_invalid_credentials(client):
    create_user(client)
    resp = login(client, password="bad")
    assert resp.status_code == 401


def test_logout_invalidates_token(client):
    create_user(client)
    tokens = login(client).json()["data"]
    token = tokens["access_token"]
    refresh = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Refresh-Token": refresh}
    client.post("/api/v1/auth/logout", headers=headers)
    resp = client.post("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_refresh_flow(client):
    create_user(client)
    data = login(client).json()["data"]
    refresh = data["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", headers={"X-Refresh-Token": refresh})
    assert resp.status_code == 200
    new_refresh = resp.json()["data"]["refresh_token"]
    # old refresh token should be revoked
    bad = client.post("/api/v1/auth/refresh", headers={"X-Refresh-Token": refresh})
    assert bad.status_code == 401
    assert "access_token" in resp.json()["data"]


def test_expired_token(client):
    create_user(client)
    from datetime import timedelta
    login_data = login(client).json()["data"]
    user_id = decode_access_token(login_data["access_token"])
    token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    resp = client.post("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_password_reset_flow(client):
    email = "reset@example.com"
    create_user(client, email=email)
    resp = client.post("/api/v1/auth/request-reset", json={"email": email})
    otp = resp.json()["data"]["otp"]
    reset = client.post("/api/v1/auth/reset-password", json={"email": email, "otp": otp, "new_password": "new"})
    assert reset.status_code == 200
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "new"})
    assert login_resp.status_code == 200


def test_email_verification_flow(client):
    email = "verify@example.com"
    create_user(client, email=email)
    resp = client.post("/api/v1/auth/request-verify", json={"email": email})
    otp = resp.json()["data"]["otp"]
    verify = client.post("/api/v1/auth/verify-email", json={"email": email, "otp": otp})
    assert verify.status_code == 200
    login_resp = login(client, email=email)
    token = login_resp.json()["data"]["access_token"]
    user_id = decode_access_token(token)
    headers = {"Authorization": f"Bearer {token}"}
    user_data = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert user_data.json()["data"]["is_verified"] is True
