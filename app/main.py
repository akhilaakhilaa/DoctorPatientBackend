from fastapi import FastAPI

from app.database import Base, engine
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.routers.auth import router as auth_router
from app.routers.doctor import router as doctor_router
from app.routers.patient import router as patient_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Doctor Patient Management API")


app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(patient_router)
@app.get("/")
def home():
    return {"message": "Doctor Patient Management API is running"}