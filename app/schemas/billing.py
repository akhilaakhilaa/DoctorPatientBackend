from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class PaymentMode(str, Enum):
    cash = "cash"
    card = "card"
    upi = "upi"


class BillingCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None

    consultation_fee: float = Field(
        ge=0,
        examples=[500.00]
    )

    additional_charges: float = Field(
        default=0,
        ge=0,
        examples=[100.00]
    )

    payment_status: PaymentStatus = PaymentStatus.pending

    payment_mode: Optional[PaymentMode] = None


class BillingUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_id: Optional[int] = None

    consultation_fee: Optional[float] = Field(
        default=None,
        ge=0
    )

    additional_charges: Optional[float] = Field(
        default=None,
        ge=0
    )

    payment_status: Optional[PaymentStatus] = None

    payment_mode: Optional[PaymentMode] = None


class BillingResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None

    consultation_fee: float
    additional_charges: float
    total_amount: float

    payment_status: PaymentStatus
    payment_mode: Optional[PaymentMode] = None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BillingPaginationResponse(BaseModel):
    total: int
    current_page: int
    limit: int
    data: list[BillingResponse]