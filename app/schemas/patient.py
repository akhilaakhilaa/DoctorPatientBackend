from pydantic import BaseModel, Field
from typing import Optional

class PatientCreate(BaseModel):
    name: str
    age: int = Field(gt=0)
    phone: str = Field(
        min_length=10,
        max_length=15,
        pattern=r"^\d{10,15}$"
    )


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    phone: str
    doctor_id: Optional[int] = None

    class Config:
        from_attributes = True