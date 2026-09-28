from typing import Optional

from pydantic import BaseModel, EmailStr


class DoctorCreate(BaseModel):
    name: str
    specialization: str
    email: EmailStr
    is_active: bool = True


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class DoctorPaginationResponse(BaseModel):
    total: int
    current_page: int
    limit: int
    data: list[DoctorResponse]