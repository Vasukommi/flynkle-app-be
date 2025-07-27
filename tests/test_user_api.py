import os

os.environ.setdefault("OPENAI_API_KEY", "test")

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
    assert resp2.json() == {"detail": "User already exists"}
