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
    engine = create_engine("sqlite:///./test_upload.db", connect_args={"check_same_thread": False})
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
    os.remove("test_upload.db")


def create_auth(client):
    client.post("/api/v1/users", json={"provider": "email", "email": "u@e.com", "password": "pwd"})
    token = client.post("/api/v1/auth/login", json={"email": "u@e.com", "password": "pwd"}).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_and_delete_upload(client, monkeypatch):
    headers = create_auth(client)
    import app.api.v1.endpoints.uploads as upload_ep

    monkeypatch.setattr(upload_ep, "upload_file_obj", lambda f: ("k1", 1))
    monkeypatch.setattr(upload_ep, "get_file_url", lambda k: f"http://minio/{k}")
    monkeypatch.setattr(upload_ep, "delete_file", lambda k: None)
    import app.core.plans as plans
    plans.PLANS["free"]["max_file_uploads"] = 1

    resp = client.post("/api/v1/uploads", headers=headers, files={"file": ("t.txt", b"x", "text/plain")})
    uid = resp.json()["data"]["upload_id"]

    lst = client.get("/api/v1/uploads", headers=headers)
    assert lst.status_code == 200
    assert len(lst.json()["data"]) == 1

    del_resp = client.delete(f"/api/v1/uploads/{uid}", headers=headers)
    assert del_resp.status_code == 200
    after = client.get("/api/v1/uploads", headers=headers)
    assert after.json()["data"] == []
