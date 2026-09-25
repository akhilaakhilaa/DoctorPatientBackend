from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user, require_admin
from app.database import get_db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorResponse
from app.schemas.patient import PatientResponse

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"]
)


# Create Doctor - Admin only
@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED
)
def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_doctor = db.query(Doctor).filter(
        Doctor.email == doctor_data.email
    ).first()

    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor email already exists"
        )

    doctor = Doctor(
        name=doctor_data.name,
        specialization=doctor_data.specialization,
        email=doctor_data.email,
        is_active=True
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return doctor


# Get all Doctors - Authenticated users
@router.get(
    "",
    response_model=list[DoctorResponse]
)
def get_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doctors = db.query(Doctor).filter(
        Doctor.is_active == True
    ).all()

    return doctors


# Get Doctor by ID - Authenticated users
@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse
)
def get_doctor(
    doctor_id: int,
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

    return doctor


# Update Doctor - Admin only
@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse
)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    existing_doctor = db.query(Doctor).filter(
        Doctor.email == doctor_data.email,
        Doctor.id != doctor_id
    ).first()

    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor email already exists"
        )

    doctor.name = doctor_data.name
    doctor.specialization = doctor_data.specialization
    doctor.email = doctor_data.email

    db.commit()
    db.refresh(doctor)

    return doctor


# Soft Delete Doctor - Admin only
@router.delete(
    "/{doctor_id}",
    response_model=DoctorResponse
)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    doctor.is_active = False

    db.commit()
    db.refresh(doctor)

    return doctor
# Assign Patient to Doctor - Admin only
@router.post(
    "/{doctor_id}/patients/{patient_id}",
    response_model=PatientResponse
)
def assign_patient_to_doctor(
    doctor_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    patient.doctor_id = doctor_id

    db.commit()
    db.refresh(patient)

    return patient


# Get Patients Assigned to Doctor
@router.get(
    "",
    response_model=list[DoctorResponse]
)
def get_doctors(
    page: int = 1,
    limit: int = 10,
    specialization: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    query = db.query(Doctor).filter(
        Doctor.is_active == True
    )

    if specialization:
        query = query.filter(
            Doctor.specialization.ilike(f"%{specialization}%")
        )

    doctors = query.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return doctors