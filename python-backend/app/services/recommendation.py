from __future__ import annotations

import os
import numpy as np
from sentence_transformers import SentenceTransformer

from ..models import Job, Student
from ..schemas import JobResponse

_GISMABERT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "gismabert")
_BASE_MODEL     = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        if os.path.isdir(_GISMABERT_PATH):
            _model = SentenceTransformer(_GISMABERT_PATH)
        else:
            _model = SentenceTransformer(_BASE_MODEL)
    return _model


def _skills_to_text(skills: list[str]) -> str:
    return ", ".join(skills) if skills else "no specific skills required"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _exact_overlap_percent(student_set: set[str], job_skills: list[str]) -> int:
    if not job_skills:
        return 0
    matched = sum(1 for s in job_skills if s.lower() in student_set)
    return int(matched / len(job_skills) * 100)


def _scale_cosine(raw: float) -> int:
    # Maps cosine range (0.30–0.90) to 0–100%
    scaled = (raw - 0.30) / 0.60 * 100
    return int(max(0, min(100, round(scaled))))


def _normalise_job(job) -> dict:
    if isinstance(job, dict):
        return {
            "id":             str(job.get("id", "")),
            "title":          job.get("title", ""),
            "company":        job.get("company", ""),
            "location":       job.get("location"),
            "job_type":       job.get("job_type"),
            "salary":         job.get("salary"),
            "posted_date":    job.get("posted_date"),
            "required_skills":job.get("required_skills") or [],
            "apply_url":      job.get("apply_url"),
            "source":         job.get("source", "seed"),
        }
    return {
        "id":             str(job.id),
        "title":          job.title,
        "company":        job.company,
        "location":       job.location,
        "job_type":       job.job_type,
        "salary":         job.salary,
        "posted_date":    job.posted_date,
        "required_skills":[s.name for s in job.required_skills],
        "apply_url":      None,
        "source":         "seed",
    }


def recommend(student: Student, jobs, filter_type: str = "all") -> list[JobResponse]:
    model = _get_model()

    student_skills = [s.name for s in student.skills]
    student_set    = {s.lower() for s in student_skills}
    student_text   = _skills_to_text(student_skills)
    student_emb    = model.encode(student_text)

    results: list[JobResponse] = []

    for raw_job in jobs:
        job = _normalise_job(raw_job)

        if filter_type and filter_type.lower() != "all":
            if (job["job_type"] or "").lower() != filter_type.lower():
                continue

        job_skills = job["required_skills"]
        job_text   = _skills_to_text(job_skills)
        job_emb    = model.encode(job_text)

        bert_score    = _cosine(student_emb, job_emb)
        match_percent = _scale_cosine(bert_score)

        missing_skills = [s for s in job_skills if s.lower() not in student_set]

        exact_pct      = _exact_overlap_percent(student_set, job_skills)
        semantic_boost = match_percent > exact_pct + 10

        results.append(JobResponse(
            id=job["id"],
            title=job["title"],
            company=job["company"],
            location=job["location"],
            job_type=job["job_type"],
            salary=job["salary"],
            posted_date=job["posted_date"],
            required_skills=job_skills,
            match_percent=match_percent,
            missing_skills=missing_skills,
            semantic_boost=semantic_boost,
            apply_url=job["apply_url"],
            source=job["source"],
        ))

    results.sort(key=lambda r: r.match_percent, reverse=True)
    return results
