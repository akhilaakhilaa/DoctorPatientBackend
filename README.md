# Doctor Patient Management API

This project is a backend application developed using FastAPI for managing Doctors and Patients. It includes authentication, authorization, database operations, doctor-patient assignment, validation, filtering, pagination, CRUD operations, soft delete and testing.

## Technologies Used

- Python 3.9+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- JWT Authentication
- Uvicorn
- Passlib
- Bcrypt
- Pytest
- Swagger / OpenAPI
- Docker

## Features

- User registration and login
- JWT based authentication
- Role based authorization
- Admin and Doctor roles
- Doctor management
- Patient management
- Doctor-patient assignment
- Doctor-patient relationship
- Complete CRUD operations
- PUT and PATCH operations
- Soft delete
- Input validation
- Doctor email uniqueness validation
- Patient phone number validation
- Doctor filtering by specialization
- Doctor filtering by active status
- Patient filtering by age
- Pagination for doctors and patients
- SQLite database
- SQLAlchemy ORM
- Automated API testing
- Swagger API documentation
- Docker support

## Project Structure

```text
DoctorPatientBackend/

│
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   └── jwt.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   └── test_api.py
│
├── screenshots/
│   ├── 01_register.png
│   ├── 02_login.png
│   ├── 03_create_doctor.png
│   ├── 04_create_patient.png
│   ├── 05_assign_patient.png
│   ├── 06_doctor_assigned_patients.png
│   └── 07_forbidden_access.png
│
├── .dockerignore
├── .env
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/akhilaakhilaa/DoctorPatientBackend.git
```

```bash
cd DoctorPatientBackend
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install required packages

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
uvicorn app.main:app --port 8002
```

The application will run at:

```text
http://127.0.0.1:8002
```

Swagger documentation:

```text
http://127.0.0.1:8002/docs
```

## Environment Configuration

Create a `.env` file in the project root.

Add:

```text
SECRET_KEY=doctor_patient_super_secret_key_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The `.env` file is added to `.gitignore` and is not uploaded to GitHub.

## Authentication

The application uses JWT authentication.

Authentication flow:

1. Register a user using `/auth/register`.
2. Login using `/auth/login`.
3. Login returns an access token.
4. Use the token in the Swagger Authorize button.
5. Access protected APIs based on the user's role.

### Register User

Endpoint:

```text
POST /auth/register
```

Example:

```json
{
    "email": "doctor@example.com",
    "password": "doctor123",
    "role": "doctor"
}
```

### Login

Endpoint:

```text
POST /auth/login
```

Example:

```json
{
    "email": "doctor@example.com",
    "password": "doctor123"
}
```

## Roles and Authorization

### Admin

Admin can:

- Create doctors
- View doctors
- Update doctors
- Patch doctors
- Soft delete doctors
- Create patients
- View patients
- Update patients
- Patch patients
- Delete patients
- Assign patients to doctors
- View assigned patients

### Doctor

Doctor can:

- Login
- View doctors
- View assigned patients
- View only their own assigned patients

A doctor cannot access patients assigned to another doctor.

## Doctor APIs

### Create Doctor

```text
POST /doctors
```

Admin only.

### Get All Doctors

```text
GET /doctors
```

Authenticated users can access this API.

Pagination and filtering are supported.

Example:

```text
GET /doctors?page=1&limit=10
```

### Get Doctor by ID

```text
GET /doctors/{doctor_id}
```

### Update Doctor

```text
PUT /doctors/{doctor_id}
```

Admin only.

### Patch Doctor

```text
PATCH /doctors/{doctor_id}
```

Admin only.

### Delete Doctor

```text
DELETE /doctors/{doctor_id}
```

Admin only.

The doctor is soft deleted by setting `is_active` to false.

## Doctor Filtering

Doctors can be filtered by specialization.

Example:

```text
GET /doctors?specialization=Cardiology
```

Doctors can also be filtered by active status.

Example:

```text
GET /doctors?is_active=true
```

Pagination can also be used with filtering.

Example:

```text
GET /doctors?specialization=Cardiology&page=1&limit=10
```

## Patient APIs

### Create Patient

```text
POST /patients
```

Authenticated users can access this API.

### Get Patients

```text
GET /patients
```

Admin can view all active patients.

Doctors can view only their assigned active patients.

Pagination is supported.

Example:

```text
GET /patients?page=1&limit=10
```

### Get Patient by ID

```text
GET /patients/{patient_id}
```

Admin can view any patient.

Doctors can view only their assigned patients.

### Update Patient

```text
PUT /patients/{patient_id}
```

### Patch Patient

```text
PATCH /patients/{patient_id}
```

### Delete Patient

```text
DELETE /patients/{patient_id}
```

The patient is soft deleted using the active status.

## Doctor-Patient Relationship

A patient contains a `doctor_id` field.

This creates a relationship between doctors and patients.

One doctor can have multiple patients.

A patient can be assigned to one doctor at a time.

## Doctor-Patient Assignment

### Assign Patient to Doctor

```text
POST /doctors/{doctor_id}/patients/{patient_id}
```

Admin only.

The API checks:

- Doctor exists
- Doctor is active
- Patient exists

A patient cannot be assigned to a non-existing doctor or inactive doctor.

### Get Doctor's Patients

```text
GET /doctors/{doctor_id}/patients
```

Admin can view any doctor's patients.

A doctor can view only their own assigned patients.

If a doctor tries to access another doctor's patients, the API returns:

```text
403 Forbidden
```

## Validation

The application uses Pydantic for request and response validation.

Validation includes:

- Doctor email must be valid.
- Doctor email must be unique.
- Duplicate doctor email returns 400 Bad Request.
- Patient age must be greater than 0.
- Patient phone number must contain exactly 10 digits.
- Patient phone number must contain numbers only.

Example valid phone number:

```text
9876543210
```

## Filtering

Doctor filtering:

```text
GET /doctors?specialization=cardiology
```

```text
GET /doctors?is_active=true
```

Patient filtering:

```text
GET /patients?age_gt=30
```

## Pagination

Doctor and Patient APIs support pagination.

Example:

```text
GET /doctors?page=1&limit=10
```

```text
GET /patients?page=1&limit=10
```

The response contains:

- total
- current_page
- limit
- data

Example response:

```json
{
    "total": 10,
    "current_page": 1,
    "limit": 10,
    "data": []
}
```

## Error Handling

HTTPException is used for handling API errors.

Common responses include:

- 400 - Bad Request
- 401 - Unauthorized
- 403 - Forbidden
- 404 - Not Found

## Database

SQLite is used as the database.

SQLAlchemy is used as the ORM.

The database contains:

- Users
- Doctors
- Patients

Patients contain a `doctor_id` field to store the assigned doctor.

The database tables are automatically created when the application starts.

The local database file is not uploaded to GitHub.

## Docker

A Dockerfile is included in the project for running the application using Docker.

The `.dockerignore` file is used to exclude unnecessary files such as:

- virtual environment
- cache files
- `.env`
- local database
- Git files

## API Flow

```text
User Registration

       ↓

User Login

       ↓

JWT Token

       ↓

Swagger Authorization

       ↓

Role Verification

       ↓

Admin Creates Doctor

       ↓

Admin Creates Patient

       ↓

Admin Assigns Patient

       ↓

Doctor Login

       ↓

Doctor Views Assigned Patients

       ↓

Unauthorized Access Returns 403
```

## Testing

Pytest is used for automated testing.

Run the tests using:

```bash
pytest -v
```

Current tests cover:

- Home endpoint
- User registration
- Invalid login
- Protected API without token

All 4 tests are passing.

The APIs were also manually tested using Swagger UI.

The following operations were tested:

- User registration
- User login
- Doctor creation
- Patient creation
- Patient assignment
- Doctor viewing assigned patients
- Forbidden access for another doctor's patients

## Screenshots

Screenshots of API testing are available in the `screenshots` folder.

The screenshots include:

1. User registration
2. User login
3. Doctor creation
4. Patient creation
5. Patient assignment
6. Doctor viewing assigned patients
7. Forbidden access

## Bonus Features

The following additional features were implemented:

- Pagination for doctors and patients
- Doctor filtering by specialization
- Doctor filtering by active status
- Patient filtering by age
- Pytest automated testing
- Swagger API documentation
- Docker support

## Assumptions

- SQLite is used for local development.
- A patient can be assigned to one doctor at a time.
- Doctor user email is matched with the doctor profile email.
- Doctors can only view their assigned patients.
- Doctors are soft deleted instead of permanently deleted.
- Patients are handled using active status for deletion.
- Passwords are stored in hashed form.
- `.env` is not committed to GitHub.
- The local SQLite database is not committed to GitHub.

## API Documentation

FastAPI provides Swagger UI for testing and documentation.

Swagger URL:

```text
http://127.0.0.1:8002/docs
```

Swagger can be used to test all available APIs including authentication, doctors, patients and doctor-patient assignments.

## GitHub Repository

https://github.com/akhilaakhilaa/DoctorPatientBackend








