from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Skill, Student
from ..schemas import SkillRequest, CVExtractResponse
from ..auth import get_current_student
from ..services import cv_parser

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


@router.post("/extract-cv", response_model=CVExtractResponse)
async def extract_skills_from_cv(
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF CV and automatically extract skills using a three-stage pipeline:

      Stage 1 — pdfplumber text extraction
      Stage 2 — Regex matching against a curated 300-term skill taxonomy
      Stage 3 — GISMABERT semantic expansion (catches paraphrases, acronyms)

    Extracted skills are auto-added to the student's profile.
    Returns the full extraction breakdown so the student can review and remove
    any skills they wish to discard.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:   # 10 MB guard
        raise HTTPException(status_code=400, detail="File too large (max 10 MB).")

    # Run the three-stage CV parsing pipeline
    result = cv_parser.parse_cv(file_bytes)

    # Auto-add discovered skills to the student's profile
    auto_added: list[str] = []
    existing_names = {s.name.lower() for s in student.skills}

    for skill_name in result["all_skills"]:
        if skill_name.lower() in existing_names:
            continue

        # Reuse existing Skill row or create a new one
        skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
            db.flush()

        student.skills.append(skill)
        existing_names.add(skill_name.lower())
        auto_added.append(skill_name)

    db.commit()
    db.refresh(student)

    return CVExtractResponse(
        all_skills=result["all_skills"],
        regex_skills=result["regex_skills"],
        semantic_skills=result["semantic_skills"],
        total_found=result["total_found"],
        cv_preview=result["cv_text"],
        auto_added=auto_added,
    )
