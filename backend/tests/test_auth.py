import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.connection import Base, get_db


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_user_registration(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "test_user"


def test_duplicate_email(client):
    user = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "Password123",
    }

    client.post("/auth/register", json=user)

    response = client.post(
        "/auth/register",
        json={
            "username": "another_user",
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered."


def test_user_login(client):
    client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_profile_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_duplicate_username(client):
    client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "first@example.com",
            "password": "Password123",
        },
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "email": "second@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken."


def test_get_current_user(client):
    client.post(
        "/auth/register",
        json={
            "username": "profile_user",
            "email": "profile@example.com",
            "password": "Password123",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "profile@example.com",
            "password": "Password123",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "profile_user"


def test_update_current_user(client):
    client.post(
        "/auth/register",
        json={
            "username": "profile_user",
            "email": "profile@example.com",
            "password": "Password123",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "profile@example.com",
            "password": "Password123",
        },
    )

    token = login.json()["access_token"]

    response = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "updated_user",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "updated_user"
    assert response.json()["email"] == "updated@example.com"


def test_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_12345"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
