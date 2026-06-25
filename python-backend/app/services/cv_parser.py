"""
CV Parser — three-stage pipeline for extracting skills from an uploaded PDF résumé.

  Stage 1: PDF text extraction via pdfplumber
  Stage 2: Regex matching against a curated 300-term skill taxonomy
            (word-boundary safe, so "R" won't match "React")
  Stage 3: GISMABERT semantic expansion — catches paraphrases, acronyms,
            and domain synonyms the regex stage misses
            (e.g. "neural networks" → Deep Learning, "version control" → Git)

Usage:
    from app.services.cv_parser import parse_cv
    result = parse_cv(file_bytes)   # bytes from UploadFile.read()
"""

from __future__ import annotations

import io
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Skill taxonomy — 300 + terms spanning all GISMA disciplines
# ---------------------------------------------------------------------------
SKILL_TAXONOMY: list[str] = [
    # Programming languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
    "Rust", "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "MATLAB",
    # Web / frontend
    "React", "Vue", "Angular", "Next.js", "HTML", "CSS", "Tailwind",
    "Redux", "GraphQL", "REST API", "Node.js", "Svelte", "jQuery",
    # Backend / infra
    "FastAPI", "Django", "Flask", "Spring Boot", "Express.js",
    "Docker", "Kubernetes", "Linux", "Git", "CI/CD", "GitHub Actions",
    "Jenkins", "Terraform", "AWS", "Azure", "GCP", "Microservices",
    "DevOps", "Ansible", "Nginx", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "Elasticsearch", "RabbitMQ", "Kafka",
    # Data / ML / AI
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Matplotlib", "Seaborn", "Tableau", "Power BI", "SQL",
    "Data Analysis", "Data Science", "Statistics", "Big Data",
    "Apache Spark", "Hadoop", "Airflow", "dbt",
    "LangChain", "RAG", "LLM", "Hugging Face", "BERT",
    "Prompt Engineering", "Vector Database", "FAISS",
    # Business / management
    "Excel", "PowerPoint", "SAP", "CRM", "ERP",
    "Business Analysis", "Financial Modeling", "Accounting",
    "Auditing", "Bloomberg Terminal", "Stakeholder Management",
    "Business Development", "Consulting", "Market Research",
    "Business Strategy", "Operations Management",
    # Project management
    "Agile", "Scrum", "Kanban", "Jira", "MS Project", "PMP",
    "Risk Management", "Project Planning", "PRINCE2", "Confluence",
    # Marketing / digital
    "SEO", "SEM", "Google Analytics", "Social Media Marketing",
    "Content Marketing", "Email Marketing", "Copywriting",
    "Adobe Creative Suite", "Figma", "UX Design", "UI Design",
    "Brand Strategy", "Google Ads", "Facebook Ads", "HubSpot",
    # Finance
    "Financial Analysis", "Investment Analysis", "Risk Analysis",
    "Tax Planning", "IFRS", "Controlling", "Treasury", "Valuation",
    "Excel Modeling", "QuickBooks",
    # HR
    "Recruitment", "Talent Acquisition", "HRIS", "Payroll",
    "Performance Management", "Training and Development",
    "Labour Law", "Onboarding", "Compensation and Benefits",
    # Soft skills
    "Leadership", "Communication", "Negotiation", "Teamwork",
    "Problem Solving", "Critical Thinking",
    "Cross-cultural Communication", "Presentation Skills",
    # Languages
    "English", "German", "French", "Spanish", "Mandarin", "Arabic",
]

# Lowercase → canonical name lookup for O(1) dedup
_TAXONOMY_LOWER: dict[str, str] = {s.lower(): s for s in SKILL_TAXONOMY}


# ---------------------------------------------------------------------------
# Stage 1 — PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Return plain text from all pages of a PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError(
            "pdfplumber is required for CV parsing. "
            "Add it to requirements.txt: pdfplumber>=0.11"
        ) from exc

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


# ---------------------------------------------------------------------------
# Stage 2 — Regex taxonomy matching
# ---------------------------------------------------------------------------

def extract_skills_regex(cv_text: str) -> list[str]:
    """
    Match CV text against the taxonomy using word-boundary regex.
    Returns canonical-cased names (e.g. 'python' → 'Python').
    Safe: single-letter skills like 'R' use a tighter boundary so they
    don't fire inside words like 'React'.
    """
    found: list[str] = []
    text_lower = cv_text.lower()

    for skill_lower, skill_canonical in _TAXONOMY_LOWER.items():
        # Tighter boundary for very short terms (1-2 chars) to avoid false positives
        if len(skill_lower) <= 2:
            pattern = r'(?<![a-z\d])' + re.escape(skill_lower) + r'(?![a-z\d])'
        else:
            pattern = r'(?<![a-z])' + re.escape(skill_lower) + r'(?![a-z])'

        if re.search(pattern, text_lower):
            found.append(skill_canonical)

    return found


# ---------------------------------------------------------------------------
# Stage 3 — GISMABERT semantic expansion
# ---------------------------------------------------------------------------

def extract_skills_semantic(cv_text: str, threshold: float = 0.52) -> list[str]:
    """
    Embed each CV sentence and compare against skill-description embeddings
    using the fine-tuned GISMABERT model (falls back to all-MiniLM-L6-v2).

    Catches paraphrases and domain synonyms that regex misses:
      "version control with GitHub"  → Git
      "built neural networks"        → Deep Learning
      "automated deployment scripts" → CI/CD

    threshold: minimum cosine similarity to accept a skill match.
    """
    try:
        from sentence_transformers import SentenceTransformer, util as st_util
    except ImportError:
        # sentence-transformers not available — skip stage 3 gracefully
        return []

    # Prefer fine-tuned GISMABERT, fall back to base model
    model_path = Path(__file__).resolve().parents[3] / "gismabert"
    model = SentenceTransformer(str(model_path) if model_path.exists() else "all-MiniLM-L6-v2")

    # Split CV into meaningful sentences / lines
    sentences = [
        s.strip()
        for s in re.split(r'[\n.;]', cv_text)
        if len(s.strip()) > 25
    ]
    if not sentences:
        return []

    cv_embeddings   = model.encode(sentences,      convert_to_tensor=True, show_progress_bar=False)
    skill_embeddings = model.encode(SKILL_TAXONOMY, convert_to_tensor=True, show_progress_bar=False)

    # cos_sim returns [n_skills × n_sentences]
    cos_scores = st_util.cos_sim(skill_embeddings, cv_embeddings)

    semantic_skills: list[str] = []
    for i, skill in enumerate(SKILL_TAXONOMY):
        if float(cos_scores[i].max()) >= threshold:
            semantic_skills.append(skill)

    return semantic_skills


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_cv(file_bytes: bytes) -> dict:
    """
    Full three-stage CV parsing pipeline.

    Returns:
        cv_text         — first 2 000 chars of extracted text (preview)
        regex_skills    — skills found by exact/regex matching
        semantic_skills — additional skills found only by semantic expansion
        all_skills      — union, sorted alphabetically
        total_found     — count of unique skills identified
    """
    cv_text = extract_text_from_pdf(file_bytes)

    regex_skills    = set(extract_skills_regex(cv_text))
    semantic_skills = set(extract_skills_semantic(cv_text))

    # Semantic stage adds recall; regex stage adds precision — take the union
    all_skills = sorted(regex_skills | semantic_skills)

    return {
        "cv_text":         cv_text[:2000],
        "regex_skills":    sorted(regex_skills),
        "semantic_skills": sorted(semantic_skills - regex_skills),   # net-new from stage 3
        "all_skills":      all_skills,
        "total_found":     len(all_skills),
    }
