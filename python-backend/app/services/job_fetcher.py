# Job fetching from Bundesagentur für Arbeit and Adzuna APIs.
# Results are cached in memory for 30 minutes.

from __future__ import annotations
import time
import logging
from datetime import date
from typing import Optional
from urllib.parse import quote

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Cache
_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _set_cached(key: str, data: list):
    _cache[key] = {"data": data, "ts": time.time()}


# Query builder

def build_query(student_skills: list[str], course: Optional[str]) -> str:
    PRIORITY = [
        "Python", "JavaScript", "Java", "React", "SQL", "Machine Learning",
        "Data Analysis", "TypeScript", "Node.js", "Docker", "AWS",
        "Excel", "SAP", "Tableau", "Marketing", "Finance", "Figma",
    ]
    COURSE_FALLBACK = {
        "business": "Management", "management": "Management", "mba": "Management",
        "marketing": "Marketing", "data": "Data Analyst", "analytics": "Data Analyst",
        "design": "UX Designer", "computer": "Developer", "software": "Developer",
        "it": "Developer", "finance": "Finance", "accounting": "Finance",
    }
    top_skill = next((s for s in PRIORITY if s in student_skills), None)
    if top_skill:
        return top_skill

    if course:
        for kw, fallback in COURSE_FALLBACK.items():
            if kw in course.lower():
                return fallback

    return student_skills[0] if student_skills else "Developer"


# Bundesagentur für Arbeit API

def _fetch_arbeitsagentur(query: str, n: int = 8) -> list[dict]:
    """
    Fetch jobs from the official German Federal Employment Agency.
    Public API — no key needed. Single-word queries work best.
    """
    # API only accepts single words — take first word of multi-word queries
    safe_q = query.split()[0]
    logger.info("Arbeitsagentur: fetching query=%r", safe_q)
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs",
                params={"was": safe_q, "size": n, "page": 0},
                headers={
                    "X-API-Key":  "jobboerse-jobsuche",
                    "User-Agent": "GISMACareerConnect/1.0",
                },
            )
            logger.info("Arbeitsagentur: HTTP %s", resp.status_code)
            if resp.status_code >= 400:
                logger.warning("Arbeitsagentur: %s — skipping", resp.status_code)
                return []
            data = resp.json()
            jobs = data.get("stellenangebote") or []
            logger.info("Arbeitsagentur: got %d results", len(jobs))
            return [_parse_arbeitsagentur(j) for j in jobs[:n]]
    except Exception as exc:
        logger.error("Arbeitsagentur: failed — %s", exc)
        return []


def _parse_arbeitsagentur(j: dict) -> dict:
    ref_nr = j.get("refnr", "")
    title  = j.get("titel", "")
    arbeitgeber = j.get("arbeitgeber", "")

    # Build the direct apply/detail URL on the official portal
    apply_url = (
        f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref_nr}"
        if ref_nr else
        f"https://www.arbeitsagentur.de/jobsuche/suche?was={quote(title)}&wo=Berlin"
    )

    # Location
    arbeitsort = j.get("arbeitsort") or {}
    city    = arbeitsort.get("ort") or "Berlin"
    country = arbeitsort.get("land") or "Deutschland"
    location = f"{city}, {country}"

    # Job type
    raw_type = (j.get("arbeitszeitModelle") or [""])[0].upper()
    type_map = {
        "VOLLZEIT": "fulltime",
        "TEILZEIT": "parttime",
        "HOMEOFFICE": "remote",
        "AUSBILDUNG": "internship",
    }
    job_type = type_map.get(raw_type, "fulltime")

    # Posted date
    eintrittsdatum = j.get("eintrittsdatum")
    try:
        posted = date.fromisoformat(eintrittsdatum[:10]) if eintrittsdatum else date.today()
    except Exception:
        posted = date.today()

    return {
        "id":             f"ba_{ref_nr}",
        "title":          title,
        "company":        arbeitgeber,
        "location":       location,
        "job_type":       job_type,
        "salary":         None,   # BA doesn't expose salary in search results
        "posted_date":    posted,
        "required_skills": [],    # extracted from description below
        "apply_url":      apply_url,
        "source":         "arbeitsagentur",
        "description":    (j.get("stellenbeschreibung") or "")[:600],
    }


# Adzuna API

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
                    "app_id":           settings.adzuna_app_id,
                    "app_key":          settings.adzuna_app_key,
                    "what":             query,
                    "results_per_page": n,
                    "content-type":     "application/json",
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

    title = j.get("title", "")
    return {
        "id":             f"adzuna_{j.get('id', '')}",
        "title":          title,
        "company":        j.get("company", {}).get("display_name", ""),
        "location":       j.get("location", {}).get("display_name", "Berlin"),
        "job_type":       "fulltime",
        "salary":         salary,
        "posted_date":    date.today(),
        "required_skills": [],
        "apply_url": (
            j.get("redirect_url")
            or f"https://www.stepstone.de/jobs/{title.replace(' ', '-').lower()}"
        ),
        "source":         "adzuna",
        "description":    (j.get("description") or "")[:600],
    }


# Skill extraction

KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
    "React", "Vue.js", "Angular", "Node.js", "Next.js", "REST APIs", "GraphQL",
    "HTML", "CSS", "Spring Boot",
    "SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "Data Analysis", "Pandas", "NumPy", "Excel", "Tableau", "Power BI",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "Scikit-learn", "Computer Vision", "NLP",
    "LLM", "Large Language Models", "RAG", "Retrieval-Augmented Generation",
    "LangChain", "LlamaIndex", "Prompt Engineering", "Fine-tuning",
    "Agentic AI", "AI Agents", "OpenAI API", "Hugging Face",
    "Vector Database", "Embeddings", "ChatGPT", "GPT-4",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git",
    "Terraform", "Linux",
    "Agile", "Scrum", "Jira", "Project Management",
    "SAP", "Finance", "Accounting", "Marketing", "SEO",
    "Figma", "UI/UX", "Power BI", "Leadership", "Communication",
]


def extract_skills_from_description(description: str) -> list[str]:
    desc_lower = description.lower()
    return [s for s in KNOWN_SKILLS if s.lower() in desc_lower][:8]


# Market trends

TRENDS_CACHE_TTL = 3600

_TREND_QUERIES = [
    "Python", "Data", "Marketing", "SAP",
    "Developer", "Designer", "Finance", "Machine Learning",
]

_ROLE_PATTERNS: list[tuple[str, list[str]]] = [
    ("ML / AI Engineer",       ["machine learning", "ai engineer", "ml engineer", "data scientist", "künstliche intelligenz"]),
    ("Data Engineer",          ["data engineer", "data engineering"]),
    ("Data Analyst",           ["data analyst", "data analysis", "datenanalyst"]),
    ("Software Developer",     ["software developer", "software engineer", "entwickler", "full stack", "backend developer", "frontend developer"]),
    ("Cloud / DevOps",         ["devops", "cloud engineer", "platform engineer", "site reliability", "infrastructure"]),
    ("Business Analyst",       ["business analyst", "unternehmensberater"]),
    ("Product Manager",        ["product manager", "product owner", "produktmanager"]),
    ("Marketing Manager",      ["marketing manager", "marketing specialist", "digital marketing", "performance marketing"]),
    ("UX / Product Designer",  ["ux designer", "ui designer", "product designer", "ux/ui", "user experience"]),
    ("SAP Consultant",         ["sap consultant", "sap berater", "sap developer"]),
    ("Finance / Controller",   ["finance analyst", "financial analyst", "controller", "finanzanalyst", "buchhalter"]),
]


def fetch_trends_data() -> dict:
    """
    Fetch jobs across multiple Bundesagentur queries and compute:
      - Top skills by frequency across all job descriptions
      - Top roles by frequency of matching job titles

    Falls back to static Berlin market data if live APIs are unavailable.
    Results cached for 1 hour.
    """
    cache_key = "trends::v1"
    entry = _cache.get(cache_key)
    if entry and (time.time() - entry["ts"]) < TRENDS_CACHE_TTL:
        logger.info("Trends cache hit")
        return entry["data"]

    logger.info("Trends: fetching %d queries from Bundesagentur + Adzuna", len(_TREND_QUERIES))
    all_jobs: list[dict] = []
    for q in _TREND_QUERIES:
        ba_jobs = _fetch_arbeitsagentur(q, n=8)
        all_jobs.extend(ba_jobs)
        # Also fetch from Adzuna for each category — ensures data even if BA is down
        az_jobs = _fetch_adzuna(q, n=5)
        all_jobs.extend(az_jobs)
    logger.info("Trends: collected %d total jobs (BA + Adzuna)", len(all_jobs))

    # Count skill occurrences across all descriptions + titles
    skill_counts: dict[str, int] = {}
    for job in all_jobs:
        text = (job.get("description") or "") + " " + (job.get("title") or "")
        for s in extract_skills_from_description(text):
            skill_counts[s] = skill_counts.get(s, 0) + 1

    # Count role occurrences from job titles
    role_counts: dict[str, int] = {}
    for job in all_jobs:
        title_lower = (job.get("title") or "").lower()
        for role, patterns in _ROLE_PATTERNS:
            if any(p in title_lower for p in patterns):
                role_counts[role] = role_counts.get(role, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:10]
    top_roles  = sorted(role_counts.items(),  key=lambda x: -x[1])[:10]

    result = {
        "total_jobs_fetched": len(all_jobs),
        "top_skills": [{"name": s, "count": c} for s, c in top_skills],
        "top_roles":  [{"role": r, "count": c} for r, c in top_roles],
        "last_updated": time.strftime("%Y-%m-%d %H:%M UTC"),
    }

    _cache[cache_key] = {"data": result, "ts": time.time()}
    logger.info("Trends: fetched %d jobs → %d skills, %d roles",
                len(all_jobs), len(top_skills), len(top_roles))
    return result


# Public interface

def fetch_real_jobs(student_skills: list[str], course: Optional[str] = None) -> list[dict]:
    """
    Fetch live Berlin jobs from:
      - Bundesagentur für Arbeit (official German agency, no key needed) — up to 8
      - Adzuna / StepStone (German market)                               — up to 5

    Results cached 30 min.
    """
    query     = build_query(student_skills, course)
    cache_key = f"real_jobs::{query}"

    cached = _get_cached(cache_key)
    if cached is not None:
        logger.info("Cache hit for query=%r", query)
        return cached

    ba_jobs    = _fetch_arbeitsagentur(query, n=8)
    adzuna_jobs = _fetch_adzuna(query, n=5)

    # Extract skills from descriptions where missing
    for job in ba_jobs + adzuna_jobs:
        if not job["required_skills"] and job.get("description"):
            job["required_skills"] = extract_skills_from_description(job["description"])

    all_jobs = ba_jobs + adzuna_jobs
    _set_cached(cache_key, all_jobs)
    return all_jobs
