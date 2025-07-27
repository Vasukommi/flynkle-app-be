import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import Base
from app.repositories import user as user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import verify_password

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_create_user_hashes_password(db):
    user_in = UserCreate(provider="email", email="test@example.com", password="secret")
    user = user_repo.create_user(db, user_in)
    assert user.password != "secret"
    assert verify_password("secret", user.password)

def test_update_user_password(db):
    user_in = UserCreate(provider="email", email="update@example.com", password="old")
    user = user_repo.create_user(db, user_in)
    user_repo.update_user(db, user, UserUpdate(password="new"))
    assert verify_password("new", user.password)
    assert not verify_password("old", user.password)
