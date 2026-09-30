import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import Base, engine

from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.billing import Billing

from app.routers.auth import router as auth_router
from app.routers.doctor import router as doctor_router
from app.routers.patient import router as patient_router
from app.routers.appointment import router as appointment_router
from app.routers.billing import router as billing_router


Base.metadata.create_all(bind=engine)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration and JWT login operations."
    },
    {
        "name": "Doctors",
        "description": "Create, view, update, delete and manage doctors."
    },
    {
        "name": "Patients",
        "description": "Create, view, update, delete and manage patients."
    },
    {
        "name": "Appointments",
        "description": "Create, view, update and manage doctor appointments."
    },
    {
        "name": "Billings",
        "description": "Manage billing and payment records."
    }
]


app = FastAPI(
    title="Doctor Patient Management API",
    description=(
        "A REST API for managing doctors, patients, appointments "
        "and billing. The API provides JWT authentication, "
        "role-based authorization, validation, audit tracking, "
        "error handling and billing management."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Doctor Patient Management Project"
    }
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Basic in-memory rate limiter

request_history = defaultdict(list)

RATE_LIMIT = 60
RATE_WINDOW = 60


@app.middleware("http")
async def rate_limit_middleware(
    request: Request,
    call_next
):
    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    current_time = time.time()

    request_history[client_ip] = [
        request_time
        for request_time in request_history[client_ip]
        if current_time - request_time < RATE_WINDOW
    ]

    if len(request_history[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": 429,
                    "message": (
                        "Too many requests. "
                        "Please try again later."
                    )
                }
            }
        )

    request_history[client_ip].append(current_time)

    response = await call_next(request)

    return response


# Uniform validation error handler

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": 422,
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


# Global exception handler

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unhandled application error"
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error"
            }
        }
    )


API_PREFIX = "/api/v1"


app.include_router(
    auth_router,
    prefix=API_PREFIX
)

app.include_router(
    doctor_router,
    prefix=API_PREFIX
)

app.include_router(
    patient_router,
    prefix=API_PREFIX
)

app.include_router(
    appointment_router,
    prefix=API_PREFIX
)

app.include_router(
    billing_router,
    prefix=API_PREFIX
)


@app.get(
    "/",
    summary="API Health Check",
    description="Checks whether the API is running."
)
def home():

    logger.info(
        "Home endpoint accessed"
    )

    return {
        "message": "Doctor Patient Management API is running",
        "version": "1.0.0"
    }