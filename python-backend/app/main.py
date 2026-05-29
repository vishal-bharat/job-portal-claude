"""
GISMA Career Connect — Python/FastAPI backend
Recommendation engine: BERT (sentence-transformers all-MiniLM-L6-v2)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

from .database import engine, Base
from .routers import auth, profile, skills, jobs

# Create all tables if they don't exist yet
# (The seed data.sql runs separately via docker-compose / Postgres init)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GISMA Career Connect API",
    description="Job recommendation system using BERT semantic matching",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(skills.router)
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok", "engine": "BERT (all-MiniLM-L6-v2)"}
