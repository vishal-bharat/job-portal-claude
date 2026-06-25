from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Job, Student
from ..schemas import JobResponse, SkillGapResponse, TrendsResponse
from ..auth import get_current_student
from ..services import recommendation, skill_gap
from ..services import job_fetcher as jf

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# Wrappers so live API job dicts work with skill_gap.analyse()
class _Skill:
    def __init__(self, name: str):
        self.name = name

class _LiveJob:
    """Wraps a raw API job dict to look like a SQLAlchemy Job ORM object."""
    def __init__(self, d: dict, idx: int):
        self.id             = 900_000 + idx   # high ID avoids collision with DB seed jobs
        self.required_skills = [_Skill(s) for s in (d.get("required_skills") or [])]


@router.get("/trends", response_model=TrendsResponse)
def market_trends(
    student: Student = Depends(get_current_student),
):
    """
    Real-time market trends from live Bundesagentur job postings.
    Queries 8 keyword categories, counts skill/role frequencies across all results.
    Cached for 1 hour — safe to call on every page load.
    """
    return jf.fetch_trends_data()


@router.get("/recommended", response_model=list[JobResponse])
def recommended_jobs(
    filter: str = Query(default="all"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns REAL jobs from Arbeitsagentur + Adzuna ranked by BERT similarity.
    No dummy seed data. If APIs return nothing, returns empty list.
    """
    student_skills = [s.name for s in student.skills]
    real_jobs = jf.fetch_real_jobs(student_skills, course=student.course)

    return recommendation.recommend(student, real_jobs, filter)


@router.get("/search", response_model=list[JobResponse])
def search_jobs(
    q: str = Query(default="Developer"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Keyword search — fetches live jobs from Arbeitsagentur + Adzuna,
    scored by BERT against the student's profile. No dummy data.
    """
    cache_key = f"search::{q}"
    cached = jf._get_cached(cache_key)

    if cached is None:
        ba_jobs     = jf._fetch_arbeitsagentur(q, n=10)
        adzuna_jobs = jf._fetch_adzuna(q, n=8)
        for job in ba_jobs + adzuna_jobs:
            if not job["required_skills"] and job.get("description"):
                job["required_skills"] = jf.extract_skills_from_description(job["description"])
        all_jobs = ba_jobs + adzuna_jobs
        jf._set_cached(cache_key, all_jobs)
    else:
        all_jobs = cached

    return recommendation.recommend(student, all_jobs, "all")


@router.get("/skill-gap", response_model=SkillGapResponse)
def skill_gap_analysis(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Skill gap analysis combines:
      - Seed jobs from DB (structured, curated skill data)
      - Live jobs from Arbeitsagentur + Adzuna (reflects current market demands)

    This means emerging skills like RAG, LangChain, Agentic AI automatically
    appear in the skill gap as soon as they become common in real job postings.
    """
    # Seed jobs from DB (always present, structured skill data)
    seed_jobs = db.query(Job).all()

    # Live jobs — extract skills from descriptions using updated KNOWN_SKILLS list
    student_skills = [s.name for s in student.skills]
    live_raw = jf.fetch_real_jobs(student_skills, course=student.course)
    for job in live_raw:
        if not job.get("required_skills") and job.get("description"):
            job["required_skills"] = jf.extract_skills_from_description(job["description"])

    # Wrap live jobs so they're compatible with skill_gap.analyse()
    live_jobs = [_LiveJob(d, i) for i, d in enumerate(live_raw) if d.get("required_skills")]

    return skill_gap.analyse(student, seed_jobs + live_jobs)
