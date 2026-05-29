"""
BERT-based job recommendation service.

How it works:
─────────────
1. Load sentence-transformers model (all-MiniLM-L6-v2, ~80MB, cached after first download).
2. Convert each skill list into a natural-language sentence:
       ["Python", "SQL", "Docker"]  →  "Python, SQL, Docker"
3. Encode both the student sentence and each job sentence into a 384-dim embedding vector.
4. Compute cosine similarity between the student vector and each job vector.
5. Scale cosine (0.0–1.0) to match percent (0–100).

Why BERT beats TF-IDF here:
────────────────────────────
- TF-IDF: "Machine Learning" and "ML" are COMPLETELY different → 0% overlap.
- BERT:   "Machine Learning" and "ML" are semantically close   → high similarity.
- BERT understands that "React developer" is related to "Frontend development"
  even if those exact words never appear in the student's skill list.

Semantic boost flag:
────────────────────
We set `semantic_boost=True` when BERT gives a higher match than a plain
exact-skill-overlap would. This lets the frontend highlight jobs where BERT
found hidden compatibility — a key thesis differentiator vs TF-IDF.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from ..models import Job, Student
from ..schemas import JobResponse


# Singleton model — loaded once at startup, reused for all requests
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
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


def recommend(student: Student, jobs: list[Job], filter_type: str = "all") -> list[JobResponse]:
    """
    Return jobs ranked by BERT cosine similarity, highest first.
    Optionally filtered by job_type.
    """
    model = _get_model()

    student_skills = [s.name for s in student.skills]
    student_set    = {s.lower() for s in student_skills}
    student_text   = _skills_to_text(student_skills)
    student_emb    = model.encode(student_text)

    results: list[JobResponse] = []

    for job in jobs:
        # Apply filter
        if filter_type and filter_type.lower() != "all":
            if (job.job_type or "").lower() != filter_type.lower():
                continue

        job_skills = [s.name for s in job.required_skills]
        job_text   = _skills_to_text(job_skills)
        job_emb    = model.encode(job_text)

        bert_score    = _cosine(student_emb, job_emb)
        match_percent = _scale_cosine(bert_score)

        # Missing skills (exact name match)
        missing_skills = [s for s in job_skills if s.lower() not in student_set]

        # Semantic boost: BERT score > exact overlap → BERT found hidden compatibility
        exact_pct    = _exact_overlap_percent(student_set, job_skills)
        semantic_boost = match_percent > exact_pct + 10

        results.append(JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            job_type=job.job_type,
            salary=job.salary,
            posted_date=job.posted_date,
            required_skills=job_skills,
            match_percent=match_percent,
            missing_skills=missing_skills,
            semantic_boost=semantic_boost,
        ))

    # Sort highest match first
    results.sort(key=lambda r: r.match_percent, reverse=True)
    return results
