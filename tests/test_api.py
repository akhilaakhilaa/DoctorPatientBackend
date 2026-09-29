from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_email(prefix):
    return f"{prefix}_{uuid4().hex[:8]}@gmail.com"


def register_user(email, password, role):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role
        }
    )

    assert response.status_code in [201, 400]


def login_user(email, password):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_home():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Doctor Patient Management API is running"
    )


def test_register_admin():
    email = unique_email("admin")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "admin123",
            "role": "admin"
        }
    )

    assert response.status_code in [201, 400]


def test_register_doctor():
    email = unique_email("doctor")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "doctor123",
            "role": "doctor"
        }
    )

    assert response.status_code in [201, 400]


def test_invalid_login():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@gmail.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_protected_doctors_without_token():
    response = client.get("/api/v1/doctors")

    assert response.status_code == 401


def test_admin_doctor_patient_flow():
    admin_email = unique_email("admin")
    doctor_email = unique_email("doctor")

    register_user(
        admin_email,
        "admin123",
        "admin"
    )

    register_user(
        doctor_email,
        "doctor123",
        "doctor"
    )

    admin_token = login_user(
        admin_email,
        "admin123"
    )

    doctor_token = login_user(
        doctor_email,
        "doctor123"
    )

    admin_headers = auth_header(admin_token)
    doctor_headers = auth_header(doctor_token)

    doctor_response = client.post(
        "/api/v1/doctors",
        headers=admin_headers,
        json={
            "name": "Test Doctor",
            "specialization": "Cardiology",
            "email": doctor_email,
            "is_active": True
        }
    )

    assert doctor_response.status_code == 201

    doctor_id = doctor_response.json()["id"]

    patient_response = client.post(
        "/api/v1/patients",
        headers=admin_headers,
        json={
            "name": "Test Patient",
            "age": 25,
            "phone": "9876543210"
        }
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    assign_response = client.post(
        f"/api/v1/doctors/{doctor_id}/patients/{patient_id}",
        headers=admin_headers
    )

    assert assign_response.status_code == 200

    get_doctor_response = client.get(
        f"/api/v1/doctors/{doctor_id}",
        headers=admin_headers
    )

    assert get_doctor_response.status_code == 200

    get_patient_response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=admin_headers
    )

    assert get_patient_response.status_code == 200

    doctor_patients = client.get(
        f"/api/v1/doctors/{doctor_id}/patients",
        headers=doctor_headers
    )

    assert doctor_patients.status_code == 200


def test_doctor_cannot_delete_doctor():
    admin_email = unique_email("admin")
    doctor_email = unique_email("doctor")

    register_user(
        admin_email,
        "admin123",
        "admin"
    )

    register_user(
        doctor_email,
        "doctor123",
        "doctor"
    )

    admin_token = login_user(
        admin_email,
        "admin123"
    )

    doctor_token = login_user(
        doctor_email,
        "doctor123"
    )

    doctor_response = client.post(
        "/api/v1/doctors",
        headers=auth_header(admin_token),
        json={
            "name": "Delete Test Doctor",
            "specialization": "Neurology",
            "email": unique_email("profile")
        }
    )

    assert doctor_response.status_code == 201

    doctor_id = doctor_response.json()["id"]

    response = client.delete(
        f"/api/v1/doctors/{doctor_id}",
        headers=auth_header(doctor_token)
    )

    assert response.status_code == 403


def test_validation_error():
    admin_email = unique_email("admin")

    register_user(
        admin_email,
        "admin123",
        "admin"
    )

    token = login_user(
        admin_email,
        "admin123"
    )

    response = client.post(
        "/api/v1/patients",
        headers=auth_header(token),
        json={
            "name": "Invalid Patient",
            "age": -5,
            "phone": "123"
        }
    )

    assert response.status_code == 422

    assert response.json()["success"] is False


def test_appointment_flow():
    admin_email = unique_email("admin")
    doctor_email = unique_email("doctor")

    register_user(
        admin_email,
        "admin123",
        "admin"
    )

    register_user(
        doctor_email,
        "doctor123",
        "doctor"
    )

    admin_token = login_user(
        admin_email,
        "admin123"
    )

    headers = auth_header(admin_token)

    doctor_response = client.post(
        "/api/v1/doctors",
        headers=headers,
        json={
            "name": "Appointment Doctor",
            "specialization": "General",
            "email": doctor_email,
            "is_active": True
        }
    )

    assert doctor_response.status_code == 201

    doctor_id = doctor_response.json()["id"]

    patient_response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "name": "Appointment Patient",
            "age": 30,
            "phone": "9123456789"
        }
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    appointment_response = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment_date": "2030-01-01T10:00:00",
            "status": "scheduled"
        }
    )

    assert appointment_response.status_code == 201

    appointment_id = appointment_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment_date": "2030-01-01T10:00:00",
            "status": "scheduled"
        }
    )

    assert duplicate_response.status_code == 400

    get_response = client.get(
        "/api/v1/appointments",
        headers=headers
    )

    assert get_response.status_code == 200

    get_one_response = client.get(
        f"/api/v1/appointments/{appointment_id}",
        headers=headers
    )

    assert get_one_response.status_code == 200

    doctor_appointments = client.get(
        f"/api/v1/appointments/doctors/{doctor_id}/appointments",
        headers=headers
    )

    assert doctor_appointments.status_code == 200

    patient_appointments = client.get(
        f"/api/v1/appointments/patients/{patient_id}/appointments",
        headers=headers
    )

    assert patient_appointments.status_code == 200

    patch_response = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        headers=headers,
        json={
            "status": "completed"
        }
    )

    assert patch_response.status_code == 200


def test_invalid_appointment_references():
    admin_email = unique_email("admin")

    register_user(
        admin_email,
        "admin123",
        "admin"
    )

    token = login_user(
        admin_email,
        "admin123"
    )

    response = client.post(
        "/api/v1/appointments",
        headers=auth_header(token),
        json={
            "doctor_id": 999999,
            "patient_id": 999999,
            "appointment_date": "2030-01-01T10:00:00",
            "status": "scheduled"
        }
    )

    assert response.status_code == 404