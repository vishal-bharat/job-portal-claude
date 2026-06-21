"""
STEP 2 — Generate training pairs for GISMABert fine-tuning.

Reads data/raw_jobs.json and produces data/training_pairs.json:
  [{"text_a": "student profile text", "text_b": "job text", "label": 0.0–1.0}, ...]

Labels are assigned by keyword overlap:
  - Same course → higher base score
  - Skill keyword matches → boosts score
  - Different course, no skill overlap → low score (hard negative)

Produces ~3,000–8,000 pairs depending on how many jobs were collected.

Run:
    python generate_pairs.py
"""

import json
import random
import re
import os

os.makedirs("data", exist_ok=True)

# ── GISMA course profiles ──────────────────────────────────────────────────────
# Each course gets: a text description + skill keywords for overlap scoring
COURSE_PROFILES = {
    "Computer Science": {
        "text": (
            "Master's student in Computer Science at GISMA University of Applied Sciences Berlin. "
            "Proficient in software development, algorithms, and system design. "
            "Skills: Python, JavaScript, Java, React, Node.js, SQL, Git, Docker, "
            "REST APIs, TypeScript, Linux, Machine Learning, Data Structures."
        ),
        "skills": [
            "python", "javascript", "java", "react", "node", "sql", "git", "docker",
            "typescript", "linux", "api", "backend", "frontend", "software", "developer",
            "programming", "code", "algorithm", "database", "cloud", "aws", "devops",
        ],
    },
    "Data Science & Analytics": {
        "text": (
            "Master's student in Data Science and Analytics at GISMA University Berlin. "
            "Experienced in statistical modelling, machine learning, and data visualisation. "
            "Skills: Python, R, SQL, TensorFlow, Pandas, Scikit-learn, Tableau, Power BI, "
            "Excel, Statistics, Data Analysis, NumPy, Matplotlib, Deep Learning."
        ),
        "skills": [
            "python", "r", "sql", "machine learning", "tensorflow", "pandas", "tableau",
            "power bi", "excel", "statistics", "data", "analyst", "scientist", "bi",
            "visualis", "sklearn", "numpy", "deep learning", "nlp", "analytics",
        ],
    },
    "Business Administration": {
        "text": (
            "Master's student in Business Administration (MBA) at GISMA University Berlin. "
            "Strong background in strategy, operations, and financial management. "
            "Skills: Excel, PowerPoint, Business Strategy, Financial Analysis, CRM, SAP, "
            "Market Research, Stakeholder Management, Business Development, Leadership."
        ),
        "skills": [
            "business", "management", "strategy", "financial", "excel", "sap", "crm",
            "operations", "analyst", "consulting", "leadership", "market", "administration",
            "mba", "stakeholder", "development", "corporate", "commercial",
        ],
    },
    "International Management": {
        "text": (
            "Master's student in International Management at GISMA University Berlin. "
            "Cross-cultural communication, global supply chains, and international strategy. "
            "Skills: Leadership, CRM, Excel, Cross-cultural Communication, Business Strategy, "
            "Supply Chain, Negotiation, International Trade, Global Operations."
        ),
        "skills": [
            "international", "global", "supply chain", "management", "leadership", "strategy",
            "cross-cultural", "negotiation", "trade", "operations", "logistics", "export",
            "multilingual", "regional", "country", "business development",
        ],
    },
    "Marketing Management": {
        "text": (
            "Master's student in Marketing Management at GISMA University Berlin. "
            "Digital marketing, brand strategy, and consumer behaviour expertise. "
            "Skills: Google Analytics, SEO, Social Media Marketing, Content Marketing, "
            "Adobe Creative Suite, CRM, Email Marketing, Copywriting, Campaign Management."
        ),
        "skills": [
            "marketing", "seo", "social media", "google analytics", "content", "brand",
            "campaign", "digital", "copywriting", "email", "crm", "advertising", "ads",
            "instagram", "facebook", "influencer", "pr", "communication",
        ],
    },
    "Finance & Accounting": {
        "text": (
            "Master's student in Finance and Accounting at GISMA University Berlin. "
            "Financial modelling, investment analysis, and management accounting. "
            "Skills: Excel, SAP, Financial Modeling, Bloomberg Terminal, SQL, Power BI, "
            "Accounting, Tax Planning, Risk Analysis, IFRS, Controlling, Auditing."
        ),
        "skills": [
            "finance", "financial", "accounting", "excel", "sap", "bloomberg", "sql",
            "controlling", "audit", "tax", "ifrs", "investment", "risk", "treasury",
            "modeling", "analyst", "kpi", "budget", "reporting", "steuer",
        ],
    },
    "Digital Business": {
        "text": (
            "Master's student in Digital Business at GISMA University Berlin. "
            "E-commerce, digital transformation, and product management. "
            "Skills: Python, SQL, Digital Marketing, UX Design, Agile, E-commerce, "
            "Analytics, Product Management, Figma, Scrum, Growth Hacking."
        ),
        "skills": [
            "digital", "product", "agile", "scrum", "ux", "e-commerce", "ecommerce",
            "figma", "growth", "transformation", "platform", "online", "startup",
            "analytics", "python", "sql", "innovation", "tech", "saas",
        ],
    },
    "Project Management": {
        "text": (
            "Master's student in Project Management at GISMA University Berlin. "
            "Agile, Scrum, and PMP methodologies with stakeholder management expertise. "
            "Skills: Agile, Scrum, Jira, MS Project, Risk Management, Excel, "
            "Leadership, Stakeholder Management, PMP, Kanban, Budget Management."
        ),
        "skills": [
            "project", "agile", "scrum", "jira", "pmp", "risk", "stakeholder",
            "kanban", "ms project", "programme", "delivery", "coordinator",
            "management", "planning", "budget", "timeline", "waterfall",
        ],
    },
    "Human Resource Management": {
        "text": (
            "Master's student in Human Resource Management at GISMA University Berlin. "
            "Talent acquisition, performance management, and employment law expertise. "
            "Skills: HRIS, Excel, Recruitment, Labour Law, Performance Management, "
            "Payroll, Training & Development, Talent Acquisition, Onboarding."
        ),
        "skills": [
            "hr", "human resource", "people", "recruitment", "talent", "payroll",
            "hris", "onboarding", "training", "development", "labour", "arbeitsrecht",
            "performance", "compensation", "benefits", "culture", "employee",
        ],
    },
}

ALL_COURSES = list(COURSE_PROFILES.keys())


def compute_label(course: str, job: dict) -> float:
    """
    Compute similarity label [0.0, 1.0] between a GISMA course profile and a job.

    High score: job is in the same domain as the course
    Low score:  job is from a completely different domain
    """
    profile = COURSE_PROFILES[course]
    text = (job["title"] + " " + job["description"]).lower()

    # Keyword overlap score
    hits = sum(1 for kw in profile["skills"] if kw in text)
    overlap = min(hits / 6, 1.0)   # normalise: 6+ hits = perfect

    # Same-course bonus — if the job was fetched under this course's queries
    same_course_bonus = 0.2 if job.get("course") == course else 0.0

    label = min(overlap + same_course_bonus, 1.0)
    return round(label, 3)


def job_to_text(job: dict) -> str:
    """Convert a job dict to a single training text."""
    return f"{job['title']}. {job['description'][:400]}"


def main():
    # Load raw jobs
    with open("data/raw_jobs.json", encoding="utf-8") as f:
        raw_jobs = json.load(f)

    print(f"📥 Loaded {len(raw_jobs)} raw job descriptions\n")

    pairs = []
    random.seed(42)

    for course, profile in COURSE_PROFILES.items():
        student_text = profile["text"]
        course_jobs  = [j for j in raw_jobs if j.get("course") == course]
        other_jobs   = [j for j in raw_jobs if j.get("course") != course]

        print(f"📚 {course}")

        # ── Positive pairs: same-course jobs ──────────────────────────────────
        for job in course_jobs:
            label = compute_label(course, job)
            pairs.append({
                "text_a": student_text,
                "text_b": job_to_text(job),
                "label":  label,
                "split":  "train",
                "type":   "positive",
            })

        # ── Hard negative pairs: jobs from different courses ───────────────────
        # Sample 40% as many negatives as positives to keep balance
        n_negatives = max(int(len(course_jobs) * 0.4), 10)
        negatives   = random.sample(other_jobs, min(n_negatives, len(other_jobs)))

        for job in negatives:
            label = compute_label(course, job)   # might still be 0.3-0.5 if overlap
            pairs.append({
                "text_a": student_text,
                "text_b": job_to_text(job),
                "label":  label,
                "split":  "train",
                "type":   "negative",
            })

        print(f"   ✅ {len(course_jobs)} positives + {len(negatives)} negatives")

    # ── Hold out 10% as evaluation set ────────────────────────────────────────
    random.shuffle(pairs)
    split_idx = int(len(pairs) * 0.9)
    for p in pairs[split_idx:]:
        p["split"] = "eval"

    # Save
    with open("data/training_pairs.json", "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)

    # Stats
    train_pairs = [p for p in pairs if p["split"] == "train"]
    eval_pairs  = [p for p in pairs if p["split"] == "eval"]
    positives   = [p for p in train_pairs if p["type"] == "positive"]
    negatives   = [p for p in train_pairs if p["type"] == "negative"]
    avg_label   = sum(p["label"] for p in pairs) / len(pairs)

    print(f"\n{'─'*50}")
    print(f"✅ Generated {len(pairs)} training pairs")
    print(f"   Train: {len(train_pairs)} | Eval: {len(eval_pairs)}")
    print(f"   Positives: {len(positives)} | Hard negatives: {len(negatives)}")
    print(f"   Avg label score: {avg_label:.3f}")
    print(f"📁 Saved to: data/training_pairs.json")
    print(f"\n{'─'*50}")
    print("Next step: Upload data/training_pairs.json to Google Colab")
    print("and run train_gismabert.py  (30 mins on free T4 GPU)")


if __name__ == "__main__":
    main()
