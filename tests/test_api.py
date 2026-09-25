from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Doctor Patient Management API is running"


def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "email": "testadmin@gmail.com",
            "password": "testadmin123",
            "role": "admin"
        }
    )

    assert response.status_code in [201, 400]


def test_invalid_login():
    response = client.post(
        "/auth/login",
        json={
            "email": "wrong@gmail.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_protected_doctors_without_token():
    response = client.get("/doctors")

    assert response.status_code == 401