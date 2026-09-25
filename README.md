# Doctor Patient Management API

This project is a backend application developed using FastAPI for managing Doctors and Patients. It includes authentication, authorization, database operations, doctor-patient assignment, validation, pagination and testing.

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

## Features

- User registration and login
- JWT based authentication
- Role based authorization
- Admin and Doctor roles
- Doctor management
- Patient management
- Doctor-patient assignment
- Input validation
- Soft delete for doctors
- Pagination
- Doctor filtering by specialization
- Automated API testing
- Swagger API documentation

## Project Structure

```text
DoctorPatientBackend/
│
├── app/
│   ├── auth/
│   │   └── jwt.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── doctor.py
│   │   └── patient.py
│   │
│   ├── services/
│   │   └── auth_service.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── tests/
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
├── .gitignore
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

http://127.0.0.1:8002

Swagger documentation:

http://127.0.0.1:8002/docs

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
- Soft delete doctors
- Create patients
- View patients
- Assign patients to doctors

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

Pagination and specialization filtering are supported.

Example:

```text
GET /doctors?page=1&limit=10
```

Filtering example:

```text
GET /doctors?specialization=Cardiology
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

### Delete Doctor

```text
DELETE /doctors/{doctor_id}
```

Admin only.

The doctor is soft deleted by setting `is_active` to false.

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

Admin can view all patients.

Doctors can view only their assigned patients.

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

## Doctor-Patient Assignment

### Assign Patient to Doctor

```text
POST /doctors/{doctor_id}/patients/{patient_id}
```

Admin only.

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
- Patient age must be greater than 0.
- Patient phone number must contain 10 to 15 digits.

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
- Pytest automated testing
- Swagger API documentation

## Assumptions

- SQLite is used for local development.
- A patient can be assigned to one doctor at a time.
- Doctor user email is matched with the doctor profile email.
- Doctors can only view their assigned patients.
- Doctors are soft deleted instead of permanently deleted.
- Passwords are stored in hashed form.
- `.env` is not committed to GitHub.
- The local SQLite database is not committed to GitHub.

## API Documentation

FastAPI provides Swagger UI for testing and documentation.

Swagger URL:

http://127.0.0.1:8002/docs

Swagger can be used to test all available APIs including authentication, doctors, patients and doctor-patient assignments.

## GitHub Repository

https://github.com/akhilaakhilaa/DoctorPatientBackend