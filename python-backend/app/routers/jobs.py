from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Job, Student
from ..schemas import JobResponse, SkillGapResponse
from ..auth import get_current_student
from ..services import recommendation, skill_gap

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/recommended", response_model=list[JobResponse])
def recommended_jobs(
    filter: str = Query(default="all"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns all jobs ranked by BERT semantic similarity to the student's skill set.
    Each job includes match_percent, missing_skills, and a semantic_boost flag.
    """
    jobs = db.query(Job).all()
    return recommendation.recommend(student, jobs, filter)


@router.get("/skill-gap", response_model=SkillGapResponse)
def skill_gap_analysis(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns the student's personalised skill gap:
    - top_missing: skills ranked by how many jobs they unlock
    - learning_path: greedy-optimal order to learn them
    """
    jobs = db.query(Job).all()
    return skill_gap.analyse(student, jobs)
