from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    name: str
    age: int = Field(gt=0)
    phone: str = Field(
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$"
    )


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$"
    )
    doctor_id: Optional[int] = None


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    phone: str
    doctor_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class PatientPaginationResponse(BaseModel):
    total: int
    current_page: int
    limit: int
    data: list[PatientResponse]