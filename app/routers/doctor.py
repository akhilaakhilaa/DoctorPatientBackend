from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user, require_admin
from app.database import get_db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.schemas.doctor import (
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorPaginationResponse
)
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


# Get Doctors with Filtering and Pagination
@router.get(
    "",
    response_model=DoctorPaginationResponse
)
def get_doctors(
    page: int = 1,
    limit: int = 10,
    specialization: str = None,
    is_active: bool = None,
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

    query = db.query(Doctor)

    # By default, show only active doctors
    if is_active is None:
        query = query.filter(
            Doctor.is_active == True
        )
    else:
        query = query.filter(
            Doctor.is_active == is_active
        )

    # Filter by specialization
    if specialization:
        query = query.filter(
            Doctor.specialization.ilike(
                f"%{specialization}%"
            )
        )

    total = query.count()

    doctors = query.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "total": total,
        "current_page": page,
        "limit": limit,
        "data": doctors
    }


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


# Partially Update Doctor - Admin only
@router.patch(
    "/{doctor_id}",
    response_model=DoctorResponse
)
def patch_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdate,
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

    if doctor_data.email is not None:
        existing_doctor = db.query(Doctor).filter(
            Doctor.email == doctor_data.email,
            Doctor.id != doctor_id
        ).first()

        if existing_doctor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor email already exists"
            )

        doctor.email = doctor_data.email

    if doctor_data.name is not None:
        doctor.name = doctor_data.name

    if doctor_data.specialization is not None:
        doctor.specialization = doctor_data.specialization

    if doctor_data.is_active is not None:
        doctor.is_active = doctor_data.is_active

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
    "/{doctor_id}/patients",
    response_model=list[PatientResponse]
)
def get_doctor_patients(
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

    # Admin can view any doctor's patients
    if current_user.role == "admin":
        return db.query(Patient).filter(
            Patient.doctor_id == doctor_id,
            Patient.is_active == True
        ).all()

    # Doctor can view only their own assigned patients
    if current_user.role == "doctor":
        if doctor.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own assigned patients"
            )

        return db.query(Patient).filter(
            Patient.doctor_id == doctor_id,
            Patient.is_active == True
        ).all()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )