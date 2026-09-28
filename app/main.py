import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient

from app.routers.auth import router as auth_router
from app.routers.doctor import router as doctor_router
from app.routers.patient import router as patient_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Doctor Patient Management API",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# API versioning
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


@app.get("/")
def home():
    logger.info("Home endpoint accessed")

    return {
        "message": "Doctor Patient Management API is running",
        "version": "1.0.0"
    }