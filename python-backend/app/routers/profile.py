from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student
from ..schemas import ProfileResponse, UpdateProfileRequest
from ..auth import get_current_student

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(student: Student = Depends(get_current_student)):
    return ProfileResponse(
        id=student.id,
        email=student.email,
        name=student.name,
        university=student.university,
        course=student.course,
        year=student.year,
        skills=[s.name for s in student.skills],
    )


@router.put("", response_model=ProfileResponse)
def update_profile(
    req: UpdateProfileRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if req.name is not None:
        student.name = req.name
    if req.university is not None:
        student.university = req.university
    if req.course is not None:
        student.course = req.course
    if req.year is not None:
        student.year = req.year

    db.commit()
    db.refresh(student)

    return ProfileResponse(
        id=student.id,
        email=student.email,
        name=student.name,
        university=student.university,
        course=student.course,
        year=student.year,
        skills=[s.name for s in student.skills],
    )
