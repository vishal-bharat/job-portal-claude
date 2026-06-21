"""
GISMABert-based job recommendation service.

How it works:
─────────────
1. Load GISMABert — a fine-tuned sentence-transformers model trained on German
   job descriptions mapped to GISMA course profiles (Bundesagentur für Arbeit data).
   Falls back to all-MiniLM-L6-v2 if GISMABert is not yet available.
2. Convert each skill list into a natural-language sentence:
       ["Python", "SQL", "Docker"]  →  "Python, SQL, Docker"
3. Encode both the student sentence and each job sentence into a 384-dim embedding vector.
4. Compute cosine similarity between the student vector and each job vector.
5. Scale cosine (0.0–1.0) to match percent (0–100).

Why GISMABert beats generic BERT here:
───────────────────────────────────────
- Generic BERT: trained on Wikipedia + BooksCorpus (general English text).
- GISMABert: fine-tuned on German job market data filtered to GISMA course domains.
  It knows that "Finanzanalyst" is closely related to "Finance & Accounting" students,
  and that a "Scrum Master" role is a strong match for Project Management graduates.

Semantic boost flag:
────────────────────
We set `semantic_boost=True` when BERT gives a higher match than a plain
exact-skill-overlap would. This lets the frontend highlight jobs where GISMABert
found hidden compatibility — a key thesis differentiator vs TF-IDF.
"""

from __future__ import annotations

import os
import numpy as np
from sentence_transformers import SentenceTransformer

from ..models import Job, Student
from ..schemas import JobResponse


# ── Model paths ────────────────────────────────────────────────────────────────
# GISMABert: fine-tuned on GISMA-course job data (run train_gismabert.py to produce)
# Falls back to generic base model if GISMABert hasn't been trained yet.
_GISMABERT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "gismabert")
_BASE_MODEL     = "all-MiniLM-L6-v2"

# Singleton model — loaded once at startup, reused for all requests
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        if os.path.isdir(_GISMABERT_PATH):
            print(f"✅ Loading GISMABert from {_GISMABERT_PATH}")
            _model = SentenceTransformer(_GISMABERT_PATH)
        else:
            print(f"ℹ️  GISMABert not found — using base model ({_BASE_MODEL})")
            print(f"   Run python-backend/collect_data.py then train_gismabert.py to train GISMABert.")
            _model = SentenceTransformer(_BASE_MODEL)
    return _model


def _skills_to_text(skills: list[str]) -> str:
    return ", ".join(skills) if skills else "no specific skills required"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalised vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _exact_overlap_percent(student_set: set[str], job_skills: list[str]) -> int:
    """Plain intersection / job-skill-count — what TF-IDF approximate."""
    if not job_skills:
        return 0
    matched = sum(1 for s in job_skills if s.lower() in student_set)
    return int(matched / len(job_skills) * 100)


def _scale_cosine(raw: float) -> int:
    """
    Scale raw BERT cosine (typically 0.25–0.95 for skill sentences) to 0–100.

    Calibration:
      raw < 0.30  →  0   (essentially no relation)
      raw = 0.60  →  50  (moderate match)
      raw >= 0.90 → 100  (near-perfect semantic match)

    Formula: clamp((raw - 0.30) / 0.60 * 100, 0, 100)
    """
    scaled = (raw - 0.30) / 0.60 * 100
    return int(max(0, min(100, round(scaled))))


def _normalise_job(job) -> dict:
    """
    Convert either a SQLAlchemy Job ORM object or a plain dict (from job_fetcher)
    into a unified dict so the scoring loop stays clean.
    """
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
    # SQLAlchemy ORM object (seed jobs — skill-gap analysis only, not shown in recommendations)
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
    """
    Return jobs ranked by BERT cosine similarity, highest first.
    Accepts either SQLAlchemy Job ORM objects or plain dicts from job_fetcher.
    Optionally filtered by job_type.
    """
    model = _get_model()

    student_skills = [s.name for s in student.skills]
    student_set    = {s.lower() for s in student_skills}
    student_text   = _skills_to_text(student_skills)
    student_emb    = model.encode(student_text)

    results: list[JobResponse] = []

    for raw_job in jobs:
        job = _normalise_job(raw_job)

        # Apply filter
        if filter_type and filter_type.lower() != "all":
            if (job["job_type"] or "").lower() != filter_type.lower():
                continue

        job_skills = job["required_skills"]
        job_text   = _skills_to_text(job_skills)
        job_emb    = model.encode(job_text)

        bert_score    = _cosine(student_emb, job_emb)
        match_percent = _scale_cosine(bert_score)

        # Missing skills (exact name match)
        missing_skills = [s for s in job_skills if s.lower() not in student_set]

        # Semantic boost: BERT score > exact overlap → BERT found hidden compatibility
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

    # Sort highest match first
    results.sort(key=lambda r: r.match_percent, reverse=True)
    return results
