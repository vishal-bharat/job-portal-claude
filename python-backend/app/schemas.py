from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional


# Auth

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    university: Optional[str] = None
    course: Optional[str] = None
    year: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    name: str
    email: str


# Profile

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None
    year: Optional[int] = None


class ProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    university: Optional[str]
    course: Optional[str]
    year: Optional[int]
    skills: list[str]

    class Config:
        from_attributes = True


# Skills

class SkillRequest(BaseModel):
    name: str


# Jobs

class SkillGapItem(BaseModel):
    """One missing skill plus how many jobs it would unlock."""
    skill: str
    unlocks_jobs: int


class JobResponse(BaseModel):
    id: str                            # str so we can use "jsearch_xxx" / "adzuna_xxx" / "1"
    title: str
    company: str
    location: Optional[str]
    job_type: Optional[str]
    salary: Optional[str]
    posted_date: Optional[date]
    required_skills: list[str]
    match_percent: int
    # BERT-specific additions
    missing_skills: list[str]          # skills in job that student doesn't have
    semantic_boost: bool               # True when BERT found semantic similarity beyond exact match
    # Real-job additions
    apply_url: Optional[str] = None    # direct apply link (LinkedIn / StepStone)
    source: Optional[str] = None       # "linkedin" | "stepstone" | "seed"

    class Config:
        from_attributes = True


class SkillGapResponse(BaseModel):
    """Global skill-gap analysis — which skills to learn next to unlock the most jobs."""
    top_missing: list[SkillGapItem]
    learning_path: list[str]           # ordered list: learn these first
    approach: str = "rag"              # greedy | semantic | rag


class CVExtractResponse(BaseModel):
    """Result of parsing an uploaded PDF CV."""
    all_skills: list[str]              # union of regex + semantic extraction
    regex_skills: list[str]            # skills found by exact taxonomy match
    semantic_skills: list[str]         # additional skills found via GISMABERT
    total_found: int
    cv_preview: str                    # first 2000 chars of extracted text
    auto_added: list[str]              # skills that were added to student profile


# Market Trends

class TrendsSkillItem(BaseModel):
    name: str
    count: int


class TrendsRoleItem(BaseModel):
    role: str
    count: int


class TrendsResponse(BaseModel):
    """
    Live market trends computed from Bundesagentur job postings.
    Skills and roles ranked by frequency across all fetched descriptions.
    """
    total_jobs_fetched: int
    top_skills: list[TrendsSkillItem]
    top_roles: list[TrendsRoleItem]
    last_updated: str


# Saved Applications

class SaveApplicationRequest(BaseModel):
    external_job_id: str
    title: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None
    apply_url: Optional[str] = None
    source: Optional[str] = "seed"


class UpdateApplicationStatusRequest(BaseModel):
    status: str    # saved | applied | interviewing | offered | rejected
    notes: Optional[str] = None


class SavedApplicationResponse(BaseModel):
    id: int
    external_job_id: str
    title: str
    company: str
    location: Optional[str]
    job_type: Optional[str]
    salary: Optional[str]
    apply_url: Optional[str]
    source: Optional[str]
    status: str
    notes: Optional[str]
    saved_at: Optional[datetime]

    class Config:
        from_attributes = True
