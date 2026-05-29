"""
Real job fetching from JSearch (LinkedIn) and Adzuna (StepStone / German market).

Architecture:
─────────────
- JSearch via RapidAPI  → LinkedIn job listings with structured skills + apply links
- Adzuna API            → StepStone and German job market listings
- In-memory cache       → 30-minute TTL so we don't hammer free-tier quotas
- Graceful fallback     → if either API fails or keys are missing, returns []
                          and the router falls back to seed jobs automatically

How to get free API keys:
──────────────────────────
JSearch:  rapidapi.com → search "JSearch" → subscribe to free plan (200 req/month)
Adzuna:   developer.adzuna.com → register → get app_id + app_key (200 req/day)

Add them to docker-compose.yml:
  JSEARCH_API_KEY: your_rapidapi_key
  ADZUNA_APP_ID:   your_adzuna_app_id
  ADZUNA_APP_KEY:  your_adzuna_app_key
"""

from __future__ import annotations
import time
import logging
from datetime import date
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# ── In-memory cache ────────────────────────────────────────────────────────────
_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes — safe for free-tier quotas


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _set_cached(key: str, data: list):
    _cache[key] = {"data": data, "ts": time.time()}


# ── Search query builder ───────────────────────────────────────────────────────

def build_query(student_skills: list[str], course: Optional[str]) -> str:
    """
    Build a job search query from the student's top 3 skills + course domain.
    Examples:
      CS student with Python, ML    → "Python Machine Learning developer Germany"
      Business student with Excel   → "Excel Business Analyst Germany"
    """
    top = student_skills[:3]
    query = " ".join(top)

    if course:
        cl = course.lower()
        if any(w in cl for w in ["business", "management", "mba", "marketing"]):
            query += " Business Analyst"
        elif any(w in cl for w in ["computer", "software", "cs", "data", "it"]):
            query += " Software Developer"

    return (query.strip() + " Germany") or "Software Developer Germany"


# ── JSearch (LinkedIn) ─────────────────────────────────────────────────────────

def _fetch_jsearch(query: str, n: int = 5) -> list[dict]:
    if not settings.jsearch_api_key:
        logger.warning("JSearch: no API key set, skipping")
        return []
    logger.info("JSearch: fetching query=%r", query)
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://jsearch.p.rapidapi.com/search",
                params={"query": query, "num_pages": "1", "date_posted": "month"},
                headers={
                    "X-RapidAPI-Key": settings.jsearch_api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
            )
            logger.info("JSearch: HTTP %s", resp.status_code)
            resp.raise_for_status()
            jobs = resp.json().get("data", [])
            logger.info("JSearch: got %d results", len(jobs))
            return [_parse_jsearch(j) for j in jobs[:n]]
    except Exception as exc:
        logger.error("JSearch: failed — %s", exc)
        return []


def _parse_jsearch(j: dict) -> dict:
    # Try structured skills first, then extract from highlights
    skills = j.get("job_required_skills") or []
    if not skills:
        qualifications = j.get("job_highlights", {}).get("Qualifications", [])
        skills = [q for q in qualifications if len(q.split()) <= 4][:6]

    min_s = j.get("job_min_salary")
    max_s = j.get("job_max_salary")
    cur   = j.get("job_salary_currency") or "€"
    salary = None
    if min_s and max_s:
        salary = f"{cur}{int(min_s):,} – {cur}{int(max_s):,}"
    elif min_s:
        salary = f"From {cur}{int(min_s):,}"

    emp_map = {"FULLTIME": "fulltime", "PARTTIME": "parttime",
               "INTERN": "internship", "CONTRACTOR": "remote"}
    job_type = emp_map.get((j.get("job_employment_type") or "").upper(), "fulltime")

    city    = j.get("job_city") or ""
    country = j.get("job_country") or ""
    location = ", ".join(filter(None, [city, country]))

    return {
        "id": f"jsearch_{j.get('job_id', '')}",
        "title": j.get("job_title", ""),
        "company": j.get("employer_name", ""),
        "location": location,
        "job_type": job_type,
        "salary": salary,
        "posted_date": date.today(),
        "required_skills": skills,
        "apply_url": j.get("job_apply_link") or j.get("job_google_link") or "",
        "source": "linkedin",
        "description": (j.get("job_description") or "")[:600],
    }


# ── Adzuna (StepStone / German market) ────────────────────────────────────────

def _fetch_adzuna(query: str, n: int = 5) -> list[dict]:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        logger.warning("Adzuna: no API keys set, skipping")
        return []
    logger.info("Adzuna: fetching query=%r", query)
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://api.adzuna.com/v1/api/jobs/de/search/1",
                params={
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "what": query,
                    "where": "Germany",
                    "results_per_page": n,
                    "content-type": "application/json",
                },
            )
            logger.info("Adzuna: HTTP %s", resp.status_code)
            resp.raise_for_status()
            jobs = resp.json().get("results", [])
            logger.info("Adzuna: got %d results", len(jobs))
            return [_parse_adzuna(j) for j in jobs[:n]]
    except Exception as exc:
        logger.error("Adzuna: failed — %s", exc)
        return []


def _parse_adzuna(j: dict) -> dict:
    min_s = j.get("salary_min")
    max_s = j.get("salary_max")
    salary = None
    if min_s and max_s:
        salary = f"€{int(min_s):,} – €{int(max_s):,}"
    elif min_s:
        salary = f"From €{int(min_s):,}"

    return {
        "id": f"adzuna_{j.get('id', '')}",
        "title": j.get("title", ""),
        "company": j.get("company", {}).get("display_name", ""),
        "location": j.get("location", {}).get("display_name", "Germany"),
        "job_type": "fulltime",
        "salary": salary,
        "posted_date": date.today(),
        "required_skills": [],  # extracted from description later
        "apply_url": j.get("redirect_url", ""),
        "source": "stepstone",
        "description": (j.get("description") or "")[:600],
    }


# ── Skill extraction from description ──────────────────────────────────────────

KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "React", "Node.js",
    "SQL", "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "AWS",
    "Machine Learning", "Deep Learning", "Data Analysis", "Pandas",
    "TensorFlow", "PyTorch", "REST APIs", "Spring Boot", "Git",
    "Agile", "Scrum", "Excel", "Tableau", "Power BI", "Figma",
    "UI/UX", "Marketing", "SEO", "Finance", "Accounting", "SAP",
    "Project Management", "Communication", "Leadership", "C++", "C#",
]


def extract_skills_from_description(description: str) -> list[str]:
    """Simple keyword match to extract known skills from a job description."""
    desc_lower = description.lower()
    found = [s for s in KNOWN_SKILLS if s.lower() in desc_lower]
    return found[:8]


# ── Main public function ───────────────────────────────────────────────────────

def fetch_real_jobs(student_skills: list[str], course: Optional[str] = None) -> list[dict]:
    """
    Fetch up to 5 jobs from JSearch (LinkedIn) + 5 from Adzuna (StepStone).
    Results are cached for 30 minutes per query.
    Returns [] gracefully if both APIs are unavailable.
    """
    query     = build_query(student_skills, course)
    cache_key = f"real_jobs::{query}"

    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    jsearch_jobs = _fetch_jsearch(query, n=5)
    adzuna_jobs  = _fetch_adzuna(query, n=5)

    # For Adzuna jobs that have no skills, extract from description
    for job in adzuna_jobs:
        if not job["required_skills"] and job.get("description"):
            job["required_skills"] = extract_skills_from_description(job["description"])

    all_jobs = jsearch_jobs + adzuna_jobs
    _set_cached(cache_key, all_jobs)
    return all_jobs
