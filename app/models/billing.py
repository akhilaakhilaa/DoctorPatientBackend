from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)

from app.database import Base


class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
        index=True
    )

    appointment_id = Column(
        Integer,
        ForeignKey("appointments.id"),
        nullable=True,
        index=True
    )

    consultation_fee = Column(
        Numeric(10, 2),
        nullable=False
    )

    additional_charges = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    payment_status = Column(
        String,
        nullable=False,
        default="pending",
        index=True
    )

    payment_mode = Column(
        String,
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index(
            "ix_billings_doctor_patient",
            "doctor_id",
            "patient_id"
        ),

        CheckConstraint(
            "consultation_fee >= 0",
            name="ck_billing_consultation_fee_nonnegative"
        ),

        CheckConstraint(
            "additional_charges >= 0",
            name="ck_billing_additional_charges_nonnegative"
        ),

        CheckConstraint(
            "total_amount >= 0",
            name="ck_billing_total_amount_nonnegative"
        ),

        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'cancelled')",
            name="ck_billing_payment_status"
        ),

        CheckConstraint(
            "payment_mode IS NULL OR payment_mode IN ('cash', 'card', 'upi')",
            name="ck_billing_payment_mode"
        ),
    )