"""
Skill Gap Analysis — four selectable approaches.

  A. greedy   (baseline)
     Exact keyword matching + Greedy Set Cover (Chvatal, 1979).
     Counts how many jobs each missing skill appears in, then greedily
     picks the skill that unlocks the most new jobs each step.
     Time complexity: O(n × m). Fast, interpretable.

  B. semantic  (GISMABERT-weighted)
     Encodes the student's profile and every job with GISMABERT
     (fine-tuned all-MiniLM-L6-v2). Missing skills are weighted by the
     cumulative cosine similarity of jobs that require them — skills
     needed by closely matching jobs rank higher.

  C. rag       (Retrieval-Augmented Skill Gap)
     Inspired by Lewis et al. (2020) RAG paper.
     Step 1 — Retrieve: embed all jobs; select the top-K most semantically
              similar to the student profile (the "retrieved context").
     Step 2 — Analyse: run frequency-weighted gap analysis only over
              that retrieved context, eliminating noise from unrelated jobs.

  D. cf        (Collaborative Filtering)
     Represents each of the 9 GISMA course programmes as a binary skill
     vector and the student as a sparse skill vector. Computes cosine
     similarity between student and every programme profile (the
     "user-item" matrix decomposition). Missing skills are weighted by
     the cumulative similarity of the programme profiles that include them
     — answers "what do students like you typically learn next?"
     Inspired by Koren, Bell & Volinsky (2009) matrix factorisation.

Production endpoint uses Semantic (highest domain coverage in evaluation).
All four approaches are available via evaluate_approaches.py for thesis comparison.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Literal

import numpy as np

from ..models import Job, Student
from ..schemas import SkillGapItem, SkillGapResponse


# ---------------------------------------------------------------------------
# Shared GISMABERT model loader — singleton, loaded once on first use
# ---------------------------------------------------------------------------

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        model_path = Path(__file__).resolve().parents[3] / "gismabert"
        _model = SentenceTransformer(
            str(model_path) if model_path.exists() else "all-MiniLM-L6-v2"
        )
    return _model


# ---------------------------------------------------------------------------
# GISMA course-skill profiles (used by Collaborative Filtering)
# These map each programme to the canonical skills graduates typically need.
# ---------------------------------------------------------------------------

COURSE_SKILL_PROFILES: dict[str, list[str]] = {
    "Computer Science": [
        "Python", "JavaScript", "TypeScript", "Java", "React", "Node.js",
        "SQL", "Git", "Docker", "Linux", "AWS", "PostgreSQL", "FastAPI", "CSS",
    ],
    "Data Science": [
        "Python", "SQL", "Machine Learning", "Data Analysis", "Tableau",
        "Power BI", "Excel", "Git", "Statistics", "NumPy", "Pandas",
    ],
    "Business Administration": [
        "Excel", "SAP", "Data Analysis", "Agile", "SQL", "Power BI",
        "CRM", "Business Strategy",
    ],
    "Finance & Accounting": [
        "Excel", "SQL", "Data Analysis", "Power BI", "SAP", "Python",
        "Financial Analysis", "Bloomberg Terminal",
    ],
    "Marketing Management": [
        "Excel", "Data Analysis", "SQL", "Tableau", "SEO",
        "Google Analytics", "Social Media Marketing", "Figma",
    ],
    "International Management": [
        "Excel", "SAP", "Data Analysis", "SQL", "Leadership",
        "Negotiation", "Supply Chain",
    ],
    "Digital Business": [
        "Python", "SQL", "Data Analysis", "Agile", "Figma",
        "React", "UX Design", "JavaScript",
    ],
    "Project Management": [
        "Agile", "Scrum", "Jira", "Risk Management", "Excel",
        "SQL", "Data Analysis", "MS Project",
    ],
    "Human Resource Management": [
        "Excel", "Recruitment", "HRIS", "Payroll",
        "Training and Development", "Performance Management", "Labour Law",
    ],
}


# ---------------------------------------------------------------------------
# Approach A — Greedy Set Cover (baseline)
# ---------------------------------------------------------------------------

def analyse_greedy(student: Student, jobs: list) -> SkillGapResponse:
    """
    Exact keyword matching + greedy set cover (Chvatal, 1979).

    For each job, collect skills the student is missing.
    Repeatedly pick the skill that unlocks the most jobs not yet accessible.

    Limitation: treats semantically related skills (e.g. PostgreSQL / MySQL)
    as completely unrelated — addressed in Approaches B and C.
    """
    student_set = {s.name.lower() for s in student.skills}

    skill_to_jobs: dict[str, set[int]] = defaultdict(set)
    for job in jobs:
        for skill in job.required_skills:
            if skill.name.lower() not in student_set:
                skill_to_jobs[skill.name].add(job.id)

    if not skill_to_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="greedy")

    sorted_skills = sorted(skill_to_jobs.items(), key=lambda x: len(x[1]), reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=len(ids))
        for name, ids in sorted_skills[:8]
    ]

    learning_path: list[str] = []
    covered: set[int] = set()
    remaining = dict(sorted_skills)

    while remaining and len(learning_path) < 6:
        best = max(remaining, key=lambda s: len(remaining[s] - covered))
        new = remaining[best] - covered
        if not new:
            break
        learning_path.append(best)
        covered |= remaining[best]
        del remaining[best]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path, approach="greedy")


# ---------------------------------------------------------------------------
# Approach B — GISMABERT Semantic Similarity
# ---------------------------------------------------------------------------

def analyse_semantic(student: Student, jobs: list) -> SkillGapResponse:
    """
    GISMABERT semantic weighting (Reimers & Gurevych, 2019).

    Encodes the student profile and each job as dense vectors.
    Missing skills are weighted by the cumulative cosine similarity of
    jobs that require them — skills demanded by closely matching jobs
    score higher than skills from loosely related postings.

    Advantage: handles semantic proximity (MySQL ≈ PostgreSQL) that
    exact keyword matching misses.
    """
    model = _get_model()

    student_text = ", ".join(s.name for s in student.skills) or "graduate student"
    if student.course:
        student_text = f"{student.course} student. Skills: {student_text}"

    student_emb = model.encode(student_text, show_progress_bar=False)

    valid_jobs, job_texts = [], []
    for job in jobs:
        skills_text = ", ".join(s.name for s in job.required_skills)
        if skills_text:
            job_texts.append(f"{getattr(job, 'title', 'Role')}. Required: {skills_text}")
            valid_jobs.append(job)

    if not valid_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="semantic")

    job_embs = model.encode(job_texts, show_progress_bar=False)

    s_n = student_emb / (np.linalg.norm(student_emb) + 1e-9)
    j_n = job_embs / (np.linalg.norm(job_embs, axis=1, keepdims=True) + 1e-9)
    sims = j_n @ s_n

    K = min(30, len(valid_jobs))
    top_idx = sims.argsort()[::-1][:K]

    student_set = {s.name.lower() for s in student.skills}
    skill_weight: dict[str, float] = defaultdict(float)
    skill_job_count: dict[str, int] = defaultdict(int)

    for i in top_idx:
        sim = float(sims[i])
        for skill in valid_jobs[i].required_skills:
            if skill.name.lower() not in student_set:
                skill_weight[skill.name] += sim
                skill_job_count[skill.name] += 1

    if not skill_weight:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="semantic")

    sorted_skills = sorted(skill_weight.items(), key=lambda x: x[1], reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=skill_job_count[name])
        for name, _ in sorted_skills[:8]
    ]
    learning_path = [name for name, _ in sorted_skills[:6]]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path, approach="semantic")


# ---------------------------------------------------------------------------
# Approach C — RAG-Inspired Retrieval + Gap Analysis
# ---------------------------------------------------------------------------

def analyse_rag(student: Student, jobs: list) -> SkillGapResponse:
    """
    Retrieval-Augmented Skill Gap (Lewis et al., 2020).

    Step 1 — Retrieve: build a flat in-memory embedding index of all jobs.
             Query with the student's profile to retrieve the top-K most
             semantically relevant jobs ("retrieved context").
    Step 2 — Analyse: run frequency-weighted greedy set cover over the
             retrieved context only, eliminating noise from unrelated postings.

    Compared to Semantic (Approach B):
    - Semantic weights skills across all top-K jobs by similarity score.
    - RAG first filters to a high-confidence retrieved set, then does
      exact frequency analysis within that context — more focused results
      for students whose profile has a clear domain signal.
    """
    model = _get_model()

    query_text = ", ".join(s.name for s in student.skills) or "graduate student"
    if student.course:
        query_text = f"{student.course} graduate. Skills: {query_text}"

    query_emb = model.encode(query_text, show_progress_bar=False)

    valid_jobs, job_texts = [], []
    for job in jobs:
        skills_text = ", ".join(s.name for s in job.required_skills)
        if skills_text:
            job_texts.append(f"{getattr(job, 'title', 'Role')}. {skills_text}")
            valid_jobs.append(job)

    if not valid_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="rag")

    job_embs = model.encode(job_texts, show_progress_bar=False)

    q_n = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    j_n = job_embs / (np.linalg.norm(job_embs, axis=1, keepdims=True) + 1e-9)
    scores = j_n @ q_n

    # Retrieve top 60 % of jobs, capped at 25 — wide enough for small corpora
    K = min(max(int(len(valid_jobs) * 0.6), 12), 25)
    retrieved = [valid_jobs[i] for i in scores.argsort()[::-1][:K]]

    student_set = {s.name.lower() for s in student.skills}
    skill_to_jobs: dict[str, set] = defaultdict(set)

    for job in retrieved:
        for skill in job.required_skills:
            if skill.name.lower() not in student_set:
                skill_to_jobs[skill.name].add(id(job))

    if not skill_to_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="rag")

    sorted_skills = sorted(skill_to_jobs.items(), key=lambda x: len(x[1]), reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=len(ids))
        for name, ids in sorted_skills[:8]
    ]

    learning_path: list[str] = []
    covered: set = set()
    remaining = dict(sorted_skills)

    while remaining and len(learning_path) < 6:
        best = max(remaining, key=lambda s: len(remaining[s] - covered))
        new = remaining[best] - covered
        if not new:
            break
        learning_path.append(best)
        covered |= remaining[best]
        del remaining[best]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path, approach="rag")


# ---------------------------------------------------------------------------
# Approach D — Collaborative Filtering
# ---------------------------------------------------------------------------

def analyse_collaborative_filtering(student: Student, jobs: list) -> SkillGapResponse:
    """
    Collaborative Filtering via course-profile matrix factorisation
    (Koren, Bell & Volinsky, 2009).

    Represents each of the 9 GISMA programmes as a binary skill vector
    and the student as a sparse skill vector. Computes cosine similarity
    between the student and each programme profile (the user-item matrix).
    Missing skills are scored by the cumulative similarity of profiles
    that include them.

    Key difference from Approaches B and C: reasoning is person-centred,
    not job-centred. Answers "what do students with a profile like yours
    typically need to learn?" rather than "what do jobs require?"

    Particular strength: cold-start — works even when the student has
    zero skills entered, falling back to the most common skills across
    all programme profiles.
    """
    # Build vocabulary of all skills across all profiles
    all_skills_ordered = sorted({
        skill
        for skills in COURSE_SKILL_PROFILES.values()
        for skill in skills
    })
    skill_idx = {s: i for i, s in enumerate(all_skills_ordered)}
    n_skills   = len(all_skills_ordered)
    profiles   = list(COURSE_SKILL_PROFILES.keys())
    n_profiles = len(profiles)

    # Build binary profile matrix  [n_profiles × n_skills]
    matrix = np.zeros((n_profiles, n_skills))
    for i, course in enumerate(profiles):
        for skill in COURSE_SKILL_PROFILES[course]:
            if skill in skill_idx:
                matrix[i, skill_idx[skill]] = 1.0

    # Build student skill vector
    student_set = {s.name.lower() for s in student.skills}
    student_vec = np.zeros(n_skills)
    for skill, idx in skill_idx.items():
        if skill.lower() in student_set:
            student_vec[idx] = 1.0

    # Cosine similarity: student ↔ each programme profile
    s_norm = np.linalg.norm(student_vec)
    if s_norm == 0:
        # Cold-start: no skills — treat all profiles as equally similar
        similarities = np.ones(n_profiles) / n_profiles
    else:
        s_n = student_vec / s_norm
        m_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        m_norms[m_norms == 0] = 1.0
        m_n = matrix / m_norms
        similarities = m_n @ s_n

    # Score each missing skill by cumulative profile similarity
    skill_score: dict[str, float] = {}
    skill_profile_count: dict[str, int] = {}

    for i, course in enumerate(profiles):
        sim = float(similarities[i])
        if sim <= 0:
            continue
        for skill in COURSE_SKILL_PROFILES[course]:
            if skill.lower() not in student_set:
                skill_score[skill]         = skill_score.get(skill, 0.0) + sim
                skill_profile_count[skill] = skill_profile_count.get(skill, 0) + 1

    if not skill_score:
        return SkillGapResponse(top_missing=[], learning_path=[], approach="cf")

    sorted_skills = sorted(skill_score.items(), key=lambda x: x[1], reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=skill_profile_count.get(name, 0))
        for name, _ in sorted_skills[:8]
    ]
    learning_path = [name for name, _ in sorted_skills[:6]]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path, approach="cf")


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

Approach = Literal["greedy", "semantic", "rag", "cf"]


def analyse(
    student: Student,
    jobs: list,
    approach: Approach = "semantic",
) -> SkillGapResponse:
    """
    Dispatcher — select skill gap approach.

    greedy   — exact keyword matching + greedy set cover (fast baseline)
    semantic — GISMABERT cosine similarity weighting  (production default)
    rag      — retrieval-augmented: retrieve context first, then analyse
    cf       — collaborative filtering via course-profile matrix
    """
    if approach == "greedy":
        return analyse_greedy(student, jobs)
    if approach == "rag":
        return analyse_rag(student, jobs)
    if approach == "cf":
        return analyse_collaborative_filtering(student, jobs)
    return analyse_semantic(student, jobs)
