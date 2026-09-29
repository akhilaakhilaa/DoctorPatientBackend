from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import get_current_user, require_admin
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse
)


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def validate_appointment_data(
    doctor_id: int,
    patient_id: int,
    appointment_date,
    db: Session,
    appointment_id: int | None = None
):
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

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    existing_query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date
    )

    if appointment_id is not None:
        existing_query = existing_query.filter(
            Appointment.id != appointment_id
        )

    existing_appointment = existing_query.first()

    if existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor already has an appointment at this time"
        )


# Create Appointment - Admin only
@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    validate_appointment_data(
        appointment_data.doctor_id,
        appointment_data.patient_id,
        appointment_data.appointment_date,
        db
    )

    appointment = Appointment(
        doctor_id=appointment_data.doctor_id,
        patient_id=appointment_data.patient_id,
        appointment_date=appointment_data.appointment_date,
        status=appointment_data.status.value,
        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment


# Get All Appointments
@router.get(
    "",
    response_model=list[AppointmentResponse]
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        return db.query(Appointment).all()

    doctor = db.query(Doctor).filter(
        Doctor.email == current_user.email,
        Doctor.is_active == True
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id
    ).all()


# Get Appointment by ID
@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    if current_user.role == "admin":
        return appointment

    doctor = db.query(Doctor).filter(
        Doctor.email == current_user.email,
        Doctor.is_active == True
    ).first()

    if not doctor or appointment.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own appointments"
        )

    return appointment


# Update Appointment - Admin only
@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    validate_appointment_data(
        appointment_data.doctor_id,
        appointment_data.patient_id,
        appointment_data.appointment_date,
        db,
        appointment_id
    )

    appointment.doctor_id = appointment_data.doctor_id
    appointment.patient_id = appointment_data.patient_id
    appointment.appointment_date = appointment_data.appointment_date
    appointment.status = appointment_data.status.value
    appointment.updated_by = current_user.id

    db.commit()
    db.refresh(appointment)

    return appointment


# Partially Update Appointment - Admin only
@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def patch_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    doctor_id = (
        appointment_data.doctor_id
        if appointment_data.doctor_id is not None
        else appointment.doctor_id
    )

    patient_id = (
        appointment_data.patient_id
        if appointment_data.patient_id is not None
        else appointment.patient_id
    )

    appointment_date = (
        appointment_data.appointment_date
        if appointment_data.appointment_date is not None
        else appointment.appointment_date
    )

    validate_appointment_data(
        doctor_id,
        patient_id,
        appointment_date,
        db,
        appointment_id
    )

    appointment.doctor_id = doctor_id
    appointment.patient_id = patient_id
    appointment.appointment_date = appointment_date

    if appointment_data.status is not None:
        appointment.status = appointment_data.status.value

    appointment.updated_by = current_user.id

    db.commit()
    db.refresh(appointment)

    return appointment


# Delete Appointment - Admin only
@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    db.delete(appointment)
    db.commit()

    return None


# Get Doctor Appointments
@router.get(
    "/doctors/{doctor_id}/appointments",
    response_model=list[AppointmentResponse]
)
def get_doctor_appointments(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    if current_user.role == "doctor":
        current_doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not current_doctor or current_doctor.id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own appointments"
            )

    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).all()


# Get Patient Appointments
@router.get(
    "/patients/{patient_id}/appointments",
    response_model=list[AppointmentResponse]
)
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    if current_user.role == "doctor":
        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or patient.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view appointments of your assigned patients"
            )

    return db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).all()