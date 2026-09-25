from pydantic import BaseModel, EmailStr


class DoctorCreate(BaseModel):
    name: str
    specialization: str
    email: EmailStr
    is_active: bool = True


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True