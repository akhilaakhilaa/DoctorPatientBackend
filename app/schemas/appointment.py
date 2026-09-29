from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus = AppointmentStatus.scheduled

    class Config:
        json_schema_extra = {
            "example": {
                "doctor_id": 1,
                "patient_id": 1,
                "appointment_date": "2030-01-15T10:00:00",
                "status": "scheduled"
            }
        }


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed"
            }
        }


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

        json_schema_extra = {
            "example": {
                "id": 1,
                "doctor_id": 1,
                "patient_id": 1,
                "appointment_date": "2030-01-15T10:00:00",
                "status": "scheduled",
                "created_at": "2026-09-29T10:00:00",
                "updated_at": "2026-09-29T10:00:00",
                "created_by": 1,
                "updated_by": 1
            }
        }