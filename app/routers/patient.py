from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import get_current_user
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientResponse


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
        phone=patient_data.phone
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


# Get Patients
# Admin can see all patients.
# Doctor can see only their assigned patients.
@router.get(
    "",
    response_model=list[PatientResponse]
)
def get_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        return db.query(Patient).all()

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

        return db.query(Patient).filter(
            Patient.doctor_id == doctor.id
        ).all()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


# Get Patient by ID
# Admin can see any patient.
# Doctor can see only their assigned patients.
@router.get(
    "",
    response_model=list[PatientResponse]
)
def get_patients(
    page: int = 1,
    limit: int = 10,
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
        query = db.query(Patient)

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
            Patient.doctor_id == doctor.id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return query.offset(
        (page - 1) * limit
    ).limit(limit).all()