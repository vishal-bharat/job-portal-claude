from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Skill, Student
from ..schemas import SkillRequest
from ..auth import get_current_student

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[str])
def all_skills(db: Session = Depends(get_db)):
    return [s.name for s in db.query(Skill).order_by(Skill.name).all()]


@router.post("", response_model=list[str])
def add_skill(
    req: SkillRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    name = req.name.strip()
    skill = db.query(Skill).filter(Skill.name.ilike(name)).first()
    if not skill:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()

    if skill not in student.skills:
        student.skills.append(skill)
        db.commit()
        db.refresh(student)

    return [s.name for s in student.skills]


@router.delete("/{skill_name}", response_model=list[str])
def remove_skill(
    skill_name: str,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    student.skills = [s for s in student.skills if s.name.lower() != skill_name.strip().lower()]
    db.commit()
    db.refresh(student)
    return [s.name for s in student.skills]
