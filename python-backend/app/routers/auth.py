from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student
from ..schemas import SignupRequest, LoginRequest, AuthResponse
from ..auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    student = Student(
        email=req.email,
        password=hash_password(req.password),
        name=req.name,
        university=req.university,
        course=req.course,
        year=req.year,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return AuthResponse(
        token=create_token(student.id),
        name=student.name,
        email=student.email,
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == req.email).first()
    if not student or not verify_password(req.password, student.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return AuthResponse(
        token=create_token(student.id),
        name=student.name,
        email=student.email,
    )
