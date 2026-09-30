from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user, require_admin
from app.database import get_db

from app.models.billing import Billing
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.user import User
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.billing import (
    BillingCreate,
    BillingUpdate,
    BillingResponse,
    BillingPaginationResponse
)


router = APIRouter(
    prefix="/billings",
    tags=["Billings"]
)


def validate_billing_data(
    patient_id: int,
    doctor_id: int,
    appointment_id: int | None,
    db: Session,
    billing_id: int | None = None
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.is_active == True
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or inactive"
        )

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is inactive"
        )

    if appointment_id is not None:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )

        if appointment.doctor_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment does not belong to the selected doctor"
            )

        if appointment.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment does not belong to the selected patient"
            )

        if appointment.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create billing for a cancelled appointment"
            )

        existing_query = db.query(Billing).filter(
            Billing.appointment_id == appointment_id,
            Billing.is_active == True
        )

        if billing_id is not None:
            existing_query = existing_query.filter(
                Billing.id != billing_id
            )

        if existing_query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Billing already exists for this appointment"
            )


@router.post(
    "",
    response_model=BillingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Billing"
)
def create_billing(
    billing_data: BillingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        # Validate patient, doctor and appointment
        validate_billing_data(
            billing_data.patient_id,
            billing_data.doctor_id,
            billing_data.appointment_id,
            db
        )

        # Calculate total amount automatically
        total_amount = (
            billing_data.consultation_fee
            + billing_data.additional_charges
        )

        # Create billing record
        billing = Billing(
            patient_id=billing_data.patient_id,
            doctor_id=billing_data.doctor_id,
            appointment_id=billing_data.appointment_id,
            consultation_fee=billing_data.consultation_fee,
            additional_charges=billing_data.additional_charges,
            total_amount=total_amount,
            payment_status=billing_data.payment_status.value,
            payment_mode=(
                billing_data.payment_mode.value
                if billing_data.payment_mode
                else None
            ),
            is_active=True
        )

        db.add(billing)

        # If billing is linked to an appointment,
        # update the appointment in the same transaction.
        if billing_data.appointment_id is not None:
            appointment = (
                db.query(Appointment)
                .filter(
                    Appointment.id == billing_data.appointment_id
                )
                .first()
            )

            if appointment is not None:
                appointment.status = "completed"

        # Flush makes SQLAlchemy send the changes to the database
        # before the final commit.
        db.flush()

        # Billing creation and appointment update
        # are committed together.
        db.commit()

        db.refresh(billing)

        return billing

    except SQLAlchemyError:
        # Roll back everything if any database operation fails.
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Billing transaction failed. No changes were saved."
        )

    except HTTPException:
        # Preserve existing validation errors such as 400/403/404.
        db.rollback()
        raise

    except Exception:
        # Roll back unexpected failures.
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating billing."
        )

@router.get(
    "",
    response_model=BillingPaginationResponse,
    summary="Get Billings with Filtering and Pagination"
)
def get_billings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    payment_status: str | None = None,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    from_date: date | None = Query(
        None,
        alias="from"
    ),
    to_date: date | None = Query(
        None,
        alias="to"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="From date cannot be after To date"
        )

    query = db.query(Billing).filter(
        Billing.is_active == True
    )

    if current_user.role == "admin":

        if payment_status:
            query = query.filter(
                Billing.payment_status == payment_status
            )

        if doctor_id:
            query = query.filter(
                Billing.doctor_id == doctor_id
            )

        if patient_id:
            query = query.filter(
                Billing.patient_id == patient_id
            )

    elif current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email,
            Doctor.is_active == True
        ).first()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found"
            )

        query = query.filter(
            Billing.doctor_id == doctor.id
        )

        if payment_status:
            query = query.filter(
                Billing.payment_status == payment_status
            )

        if patient_id:
            query = query.filter(
                Billing.patient_id == patient_id
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if from_date:
        start_datetime = datetime.combine(
            from_date,
            time.min
        )

        query = query.filter(
            Billing.created_at >= start_datetime
        )

    if to_date:
        end_datetime = datetime.combine(
            to_date + timedelta(days=1),
            time.min
        )

        query = query.filter(
            Billing.created_at < end_datetime
        )

    total = query.count()

    billings = query.order_by(
        Billing.created_at.desc()
    ).offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "total": total,
        "current_page": page,
        "limit": limit,
        "data": billings
    }


@router.get(
    "/reports/revenue",
    summary="Get Revenue Report"
)
def revenue_report(
    doctor_id: int | None = None,
    from_date: date | None = Query(
        None,
        alias="from"
    ),
    to_date: date | None = Query(
        None,
        alias="to"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="From date cannot be after To date"
        )

    query = db.query(Billing).filter(
        Billing.is_active == True,
        Billing.payment_status == "paid"
    )

    if doctor_id:
        query = query.filter(
            Billing.doctor_id == doctor_id
        )

    if from_date:
        start_datetime = datetime.combine(
            from_date,
            time.min
        )

        query = query.filter(
            Billing.created_at >= start_datetime
        )

    if to_date:
        end_datetime = datetime.combine(
            to_date + timedelta(days=1),
            time.min
        )

        query = query.filter(
            Billing.created_at < end_datetime
        )

    total_revenue = query.with_entities(
        func.coalesce(
            func.sum(Billing.total_amount),
            0
        )
    ).scalar()

    daily_rows = query.with_entities(
        func.date(Billing.created_at).label("date"),
        func.coalesce(
            func.sum(Billing.total_amount),
            0
        ).label("revenue")
    ).group_by(
        func.date(Billing.created_at)
    ).order_by(
        func.date(Billing.created_at)
    ).all()

    daily_revenue = [
        {
            "date": str(row.date),
            "revenue": float(row.revenue)
        }
        for row in daily_rows
    ]

    return {
        "doctor_id": doctor_id,
        "from": str(from_date) if from_date else None,
        "to": str(to_date) if to_date else None,
        "total_revenue": float(total_revenue),
        "daily_revenue": daily_revenue
    }


@router.get(
    "/{billing_id}",
    response_model=BillingResponse,
    summary="Get Billing by ID"
)
def get_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.is_active == True
    ).first()

    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing not found"
        )

    if current_user.role == "admin":
        return billing

    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email,
            Doctor.is_active == True
        ).first()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found"
            )

        if billing.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own patient billings"
            )

        return billing

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


@router.get(
    "/patients/{patient_id}/billings",
    response_model=BillingPaginationResponse,
    summary="Get Patient Billings"
)
def get_patient_billings(
    patient_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.is_active == True
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email,
            Doctor.is_active == True
        ).first()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found"
            )

        if patient.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view billings of your assigned patients"
            )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    query = db.query(Billing).filter(
        Billing.patient_id == patient_id,
        Billing.is_active == True
    )

    total = query.count()

    billings = query.order_by(
        Billing.created_at.desc()
    ).offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "total": total,
        "current_page": page,
        "limit": limit,
        "data": billings
    }


@router.get(
    "/doctors/{doctor_id}/billings",
    response_model=BillingPaginationResponse,
    summary="Get Doctor Billings"
)
def get_doctor_billings(
    doctor_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.is_active == True
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    if current_user.role == "doctor":

        current_doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email,
            Doctor.is_active == True
        ).first()

        if not current_doctor or current_doctor.id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own billings"
            )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    query = db.query(Billing).filter(
        Billing.doctor_id == doctor_id,
        Billing.is_active == True
    )

    total = query.count()

    billings = query.order_by(
        Billing.created_at.desc()
    ).offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "total": total,
        "current_page": page,
        "limit": limit,
        "data": billings
    }


@router.put(
    "/{billing_id}",
    response_model=BillingResponse,
    summary="Update Billing"
)
def update_billing(
    billing_id: int,
    billing_data: BillingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.is_active == True
    ).first()

    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing not found"
        )

    validate_billing_data(
        billing_data.patient_id,
        billing_data.doctor_id,
        billing_data.appointment_id,
        db,
        billing_id
    )

    billing.patient_id = billing_data.patient_id
    billing.doctor_id = billing_data.doctor_id
    billing.appointment_id = billing_data.appointment_id
    billing.consultation_fee = billing_data.consultation_fee
    billing.additional_charges = billing_data.additional_charges

    billing.total_amount = (
        billing_data.consultation_fee
        + billing_data.additional_charges
    )

    billing.payment_status = billing_data.payment_status.value

    billing.payment_mode = (
        billing_data.payment_mode.value
        if billing_data.payment_mode
        else None
    )

    db.commit()
    db.refresh(billing)

    return billing


@router.patch(
    "/{billing_id}",
    response_model=BillingResponse,
    summary="Patch Billing"
)
def patch_billing(
    billing_id: int,
    billing_data: BillingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.is_active == True
    ).first()

    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing not found"
        )

    patient_id = (
        billing_data.patient_id
        if billing_data.patient_id is not None
        else billing.patient_id
    )

    doctor_id = (
        billing_data.doctor_id
        if billing_data.doctor_id is not None
        else billing.doctor_id
    )

    appointment_id = (
        billing_data.appointment_id
        if billing_data.appointment_id is not None
        else billing.appointment_id
    )

    validate_billing_data(
        patient_id,
        doctor_id,
        appointment_id,
        db,
        billing_id
    )

    billing.patient_id = patient_id
    billing.doctor_id = doctor_id
    billing.appointment_id = appointment_id

    if billing_data.consultation_fee is not None:
        billing.consultation_fee = billing_data.consultation_fee

    if billing_data.additional_charges is not None:
        billing.additional_charges = billing_data.additional_charges

    billing.total_amount = (
        float(billing.consultation_fee)
        + float(billing.additional_charges)
    )

    if billing_data.payment_status is not None:
        billing.payment_status = billing_data.payment_status.value

    if billing_data.payment_mode is not None:
        billing.payment_mode = billing_data.payment_mode.value

    db.commit()
    db.refresh(billing)

    return billing


@router.delete(
    "/{billing_id}",
    response_model=BillingResponse,
    summary="Soft Delete Billing"
)
def delete_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    billing = db.query(Billing).filter(
        Billing.id == billing_id,
        Billing.is_active == True
    ).first()

    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing not found"
        )

    billing.is_active = False

    db.commit()
    db.refresh(billing)

    return billing