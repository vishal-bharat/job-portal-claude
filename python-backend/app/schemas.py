from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Profile ───────────────────────────────────────────────────────────────────

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


# ── Skills ────────────────────────────────────────────────────────────────────

class SkillRequest(BaseModel):
    name: str


# ── Jobs ──────────────────────────────────────────────────────────────────────

class SkillGapItem(BaseModel):
    """One missing skill plus how many jobs it would unlock."""
    skill: str
    unlocks_jobs: int


class JobResponse(BaseModel):
    id: int
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

    class Config:
        from_attributes = True


class SkillGapResponse(BaseModel):
    """Global skill-gap analysis — which skills to learn next to unlock the most jobs."""
    top_missing: list[SkillGapItem]
    learning_path: list[str]           # ordered list: learn these first
