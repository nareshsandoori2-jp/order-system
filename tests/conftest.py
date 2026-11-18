import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

load_dotenv()

from app import models  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
assert TEST_DATABASE_URL and "test" in TEST_DATABASE_URL, (
    "Set TEST_DATABASE_URL to a database whose name contains 'test'"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def make_user(client, email, role="customer"):
    client.post(
        "/auth/signup",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    if role == "admin":
        with TestingSession() as db:
            db.execute(
                update(models.User)
                .where(models.User.email == email)
                .values(role="admin")
            )
            db.commit()
    response = client.post(
        "/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def user_headers(client):
    return make_user(client, "user@example.com")


@pytest.fixture
def admin_headers(client):
    return make_user(client, "admin@example.com", role="admin")