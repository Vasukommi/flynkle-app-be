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


def create_user(client, email, is_admin=False):
    data = {"provider": "email", "email": email, "password": "pwd"}
    if is_admin:
        data["is_admin"] = True
    resp = client.post("/api/v1/users", json=data)
    return resp.json()["data"]["user_id"]


def test_admin_required(client):
    user_id = create_user(client, "user@example.com", is_admin=False)
    headers = {"X-User-ID": user_id}
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["message"] == "Admin privileges required"


def test_admin_can_access(client):
    admin_id = create_user(client, "admin@example.com", is_admin=True)
    headers = {"X-User-ID": admin_id}
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 200

