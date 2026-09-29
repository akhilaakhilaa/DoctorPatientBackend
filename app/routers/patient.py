from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import get_current_user, require_admin
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientPaginationResponse
)


router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


# Create Patient - Authenticated users
@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = Patient(
        name=patient_data.name,
        age=patient_data.age,
        phone=patient_data.phone,
        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


# Get Patients with Filtering and Pagination
@router.get(
    "",
    response_model=PatientPaginationResponse
)
def get_patients(
    page: int = 1,
    limit: int = 10,
    age_gt: int = None,
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

    if current_user.role == "admin":
        query = db.query(Patient).filter(
            Patient.is_active == True
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

        query = db.query(Patient).filter(
            Patient.doctor_id == doctor.id,
            Patient.is_active == True
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if age_gt is not None:
        query = query.filter(
            Patient.age > age_gt
        )

    total = query.count()

    patients = query.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "total": total,
        "current_page": page,
        "limit": limit,
        "data": patients
    }


# Get Patient by ID
@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
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

    if current_user.role == "admin":
        return patient

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
                detail="You can only view your assigned patients"
            )

        return patient

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


# Update Patient - Admin only
@router.put(
    "/{patient_id}",
    response_model=PatientResponse
)
def update_patient(
    patient_id: int,
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    patient.name = patient_data.name
    patient.age = patient_data.age
    patient.phone = patient_data.phone
    patient.updated_by = current_user.id

    db.commit()
    db.refresh(patient)

    return patient


# Partially Update Patient - Admin only
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse
)
def patch_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    if patient_data.name is not None:
        patient.name = patient_data.name

    if patient_data.age is not None:
        patient.age = patient_data.age

    if patient_data.phone is not None:
        patient.phone = patient_data.phone

    if patient_data.doctor_id is not None:
        doctor = db.query(Doctor).filter(
            Doctor.id == patient_data.doctor_id,
            Doctor.is_active == True
        ).first()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found or inactive"
            )

        patient.doctor_id = patient_data.doctor_id

    patient.updated_by = current_user.id

    db.commit()
    db.refresh(patient)

    return patient


# Soft Delete Patient - Admin only
@router.delete(
    "/{patient_id}",
    response_model=PatientResponse
)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
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

    patient.is_active = False
    patient.updated_by = current_user.id

    db.commit()
    db.refresh(patient)

    return patient