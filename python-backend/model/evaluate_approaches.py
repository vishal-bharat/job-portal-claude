"""
Skill Gap Approach Comparison — standalone evaluation script.
Tests all four approaches: Greedy, Semantic (GISMABERT), RAG, Collaborative Filtering.

No running database required — uses the SEED_JOBS corpus directly.
Semantic / RAG use TF-IDF cosine similarity as a proxy when GISMABERT is
not available; run locally with the trained model for final thesis numbers.

Metrics:
  Dom.Precision  — % of top-5 suggested skills that belong to the student's domain
  Full.Coverage  — % of ALL 36 seed jobs the 6-skill learning path unlocks
  Dom.Coverage   — % of domain-specific jobs the learning path unlocks
  Time (ms)      — wall-clock response time in milliseconds

Run:
    cd python-backend
    python model/evaluate_approaches.py
"""

from __future__ import annotations

import sys
import time
import textwrap
from collections import defaultdict
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Minimal mock objects (mirror ORM interface expected by skill_gap.py)
# ---------------------------------------------------------------------------

class _Skill:
    def __init__(self, name: str): self.name = name

class _Student:
    _c = 0
    def __init__(self, label: str, course: str, skills: list[str]):
        _Student._c += 1
        self.id     = _Student._c
        self.label  = label
        self.course = course
        self.skills = [_Skill(s) for s in skills]

class _Job:
    _c = 0
    def __init__(self, title: str, skills: list[str], domain: str):
        _Job._c += 1
        self.id              = _Job._c
        self.title           = title
        self.required_skills = [_Skill(s) for s in skills]
        self.domain          = domain


# ---------------------------------------------------------------------------
# Seed job corpus
# ---------------------------------------------------------------------------

_RAW = [
    ("Backend Python Developer",    ["Python","FastAPI","PostgreSQL","Docker","Git"],            "Computer Science"),
    ("Full Stack Developer",        ["React","Node.js","TypeScript","SQL","Git"],                "Computer Science"),
    ("Software Engineer Intern",    ["Java","SQL","Git","Agile"],                               "Computer Science"),
    ("DevOps Engineer",             ["Docker","AWS","Git","Python","Linux"],                    "Computer Science"),
    ("Frontend Developer",          ["React","JavaScript","TypeScript","CSS","Git"],            "Computer Science"),
    ("Cloud Engineer",              ["AWS","Docker","Python","Linux","Git"],                    "Computer Science"),
    ("Mobile Developer (Android)",  ["Java","Git","SQL","Agile"],                               "Computer Science"),
    ("Junior Software Developer",   ["Python","JavaScript","SQL","Git"],                        "Computer Science"),
    ("Data Scientist",              ["Python","Machine Learning","SQL","Data Analysis","Git"],  "Data Science"),
    ("Machine Learning Engineer",   ["Python","Machine Learning","Docker","SQL","Git"],         "Data Science"),
    ("Data Analyst",                ["SQL","Python","Excel","Tableau","Data Analysis"],         "Data Science"),
    ("BI Analyst",                  ["SQL","Power BI","Excel","Data Analysis"],                 "Data Science"),
    ("Data Engineer",               ["Python","SQL","Docker","AWS","Git"],                      "Data Science"),
    ("Data Science Intern",         ["Python","Machine Learning","SQL","Data Analysis"],        "Data Science"),
    ("Analytics Engineer",          ["SQL","Python","Data Analysis","Git"],                     "Data Science"),
    ("Business Analyst",            ["Excel","SQL","Data Analysis","Power BI","Agile"],         "Business Administration"),
    ("Management Consultant",       ["Excel","Data Analysis","Agile","SAP"],                   "Business Administration"),
    ("Operations Manager",          ["Excel","SAP","Data Analysis","Agile"],                   "Business Administration"),
    ("Strategy Analyst Intern",     ["Excel","Data Analysis","SQL"],                           "Business Administration"),
    ("Project Manager",             ["Agile","Excel","SAP","Data Analysis"],                   "Business Administration"),
    ("Financial Analyst",           ["Excel","SQL","Data Analysis","Power BI"],                "Finance"),
    ("Investment Banking Analyst",  ["Excel","Data Analysis","SQL"],                           "Finance"),
    ("Finance Intern",              ["Excel","SAP","Data Analysis"],                           "Finance"),
    ("Risk Analyst",                ["SQL","Excel","Python","Data Analysis"],                   "Finance"),
    ("Digital Marketing Analyst",   ["Excel","Data Analysis","SQL","Tableau"],                 "Marketing"),
    ("Marketing Manager",           ["Excel","Data Analysis","Agile"],                         "Marketing"),
    ("Growth Marketing Intern",     ["Excel","Data Analysis","SQL"],                           "Marketing"),
    ("UX Designer",                 ["Figma","JavaScript","Agile","Git"],                      "Digital Business"),
    ("Product Manager",             ["Agile","SQL","Data Analysis","Figma"],                   "Digital Business"),
    ("Product Designer Intern",     ["Figma","Agile"],                                         "Digital Business"),
    ("Supply Chain Analyst",        ["Excel","SAP","Data Analysis","SQL"],                     "International Management"),
    ("Logistics Manager",           ["SAP","Excel","Data Analysis"],                           "International Management"),
    ("International Trade Analyst", ["Excel","SAP","Data Analysis","SQL"],                     "International Management"),
    ("Remote Python Developer",     ["Python","SQL","Docker","Git"],                           "Computer Science"),
    ("Part-time Data Analyst",      ["SQL","Excel","Data Analysis","Tableau"],                 "Data Science"),
    ("Freelance Frontend Dev",      ["React","JavaScript","TypeScript","CSS"],                 "Computer Science"),
]
ALL_JOBS = [_Job(t, s, d) for t, s, d in _RAW]


# ---------------------------------------------------------------------------
# Domain skill taxonomy (ground truth for Domain Precision)
# ---------------------------------------------------------------------------

DOMAIN_SKILLS: dict[str, set[str]] = {
    "Computer Science":        {"Python","JavaScript","TypeScript","Java","React","Node.js","Docker","AWS","Git","Linux","SQL","FastAPI","PostgreSQL","CSS"},
    "Data Science":            {"Python","Machine Learning","SQL","Data Analysis","Tableau","Power BI","Excel","NumPy","Pandas","TensorFlow","Statistics"},
    "Business Administration": {"Excel","SAP","Data Analysis","Agile","Power BI","SQL","CRM","Business Strategy"},
    "Finance":                 {"Excel","SQL","Data Analysis","Power BI","SAP","Python","Financial Analysis"},
    "Marketing":               {"Excel","Data Analysis","SQL","Tableau","Agile","Figma","SEO","Google Analytics"},
    "Digital Business":        {"Figma","Agile","SQL","Data Analysis","JavaScript","Python","React","UX Design"},
    "International Management":{"Excel","SAP","Data Analysis","SQL","Supply Chain","Leadership"},
}


# ---------------------------------------------------------------------------
# Test student profiles
# ---------------------------------------------------------------------------

TEST_STUDENTS = [
    _Student("Vishal — CS",      "Computer Science",        ["Python", "Git"]),
    _Student("Priya — DS",       "Data Science",            ["Python", "SQL"]),
    _Student("Leon — MBA",       "Business Administration", ["Excel", "Agile"]),
    _Student("Sara — Finance",   "Finance",                 ["Excel"]),
    _Student("Cold-start (no skills)", "Computer Science",  []),   # cold-start edge case
]


# ---------------------------------------------------------------------------
# GISMA course profiles (Collaborative Filtering matrix)
# ---------------------------------------------------------------------------

COURSE_SKILL_PROFILES: dict[str, list[str]] = {
    "Computer Science":        ["Python","JavaScript","TypeScript","Java","React","Node.js","SQL","Git","Docker","Linux","AWS","PostgreSQL","FastAPI","CSS"],
    "Data Science":            ["Python","SQL","Machine Learning","Data Analysis","Tableau","Power BI","Excel","Git","Statistics","NumPy","Pandas"],
    "Business Administration": ["Excel","SAP","Data Analysis","Agile","SQL","Power BI","CRM","Business Strategy"],
    "Finance & Accounting":    ["Excel","SQL","Data Analysis","Power BI","SAP","Python","Financial Analysis","Bloomberg Terminal"],
    "Marketing Management":    ["Excel","Data Analysis","SQL","Tableau","SEO","Google Analytics","Social Media Marketing","Figma"],
    "International Management":["Excel","SAP","Data Analysis","SQL","Leadership","Negotiation","Supply Chain"],
    "Digital Business":        ["Python","SQL","Data Analysis","Agile","Figma","React","UX Design","JavaScript"],
    "Project Management":      ["Agile","Scrum","Jira","Risk Management","Excel","SQL","Data Analysis","MS Project"],
    "Human Resource Management":["Excel","Recruitment","HRIS","Payroll","Training and Development","Performance Management","Labour Law"],
}


# ---------------------------------------------------------------------------
# Approach implementations (standalone — no FastAPI imports)
# ---------------------------------------------------------------------------

def _greedy(student: _Student, jobs: list[_Job]) -> tuple[list[str], list[str]]:
    have = {s.name.lower() for s in student.skills}
    s2j: dict[str, set[int]] = defaultdict(set)
    for j in jobs:
        for sk in j.required_skills:
            if sk.name.lower() not in have:
                s2j[sk.name].add(j.id)
    if not s2j:
        return [], []
    ss = sorted(s2j.items(), key=lambda x: len(x[1]), reverse=True)
    path, covered, rem = [], set(), dict(ss)
    while rem and len(path) < 6:
        best = max(rem, key=lambda s: len(rem[s] - covered))
        if not (rem[best] - covered):
            break
        path.append(best); covered |= rem[best]; del rem[best]
    return [n for n, _ in ss[:5]], path


def _build_tfidf(docs: list[str]):
    """Simple TF-IDF vectoriser (proxy for sentence-transformers)."""
    vocab: dict[str, int] = {}
    for doc in docs:
        for w in doc.lower().split():
            if w not in vocab:
                vocab[w] = len(vocab)
    N = len(docs)
    df = np.zeros(len(vocab))
    tokenised = []
    for doc in docs:
        words = doc.lower().split()
        tokenised.append(words)
        seen = set(words)
        for w in seen:
            if w in vocab:
                df[vocab[w]] += 1
    idf = np.log((N + 1) / (df + 1)) + 1

    def vectorise(text: str) -> np.ndarray:
        v = np.zeros(len(vocab))
        words = text.lower().split()
        for w in words:
            if w in vocab:
                v[vocab[w]] += 1
        if words:
            v /= len(words)
        v *= idf
        n = np.linalg.norm(v)
        return v / n if n > 0 else v

    return vectorise


def _try_load_model():
    """Load GISMABERT if available, else return None (falls back to TF-IDF)."""
    try:
        from sentence_transformers import SentenceTransformer
        model_path = Path(__file__).resolve().parents[1] / "gismabert"
        m = SentenceTransformer(str(model_path) if model_path.exists() else "all-MiniLM-L6-v2")
        return m
    except Exception:
        return None


_MODEL = None
_MODEL_CHECKED = False

def _encode(texts: list[str]) -> np.ndarray:
    """Encode texts using GISMABERT or TF-IDF proxy."""
    global _MODEL, _MODEL_CHECKED
    if not _MODEL_CHECKED:
        _MODEL = _try_load_model()
        _MODEL_CHECKED = True
        if _MODEL:
            print("  [encoder] GISMABERT loaded — using real embeddings")
        else:
            print("  [encoder] GISMABERT unavailable — using TF-IDF proxy")
    if _MODEL:
        return _MODEL.encode(texts, show_progress_bar=False)
    # TF-IDF proxy
    vec = _build_tfidf(texts)
    return np.array([vec(t) for t in texts])


def _student_text(student: _Student) -> str:
    skills = ", ".join(s.name for s in student.skills) or "no skills"
    return f"{student.course} student. Skills: {skills}"


def _semantic(student: _Student, jobs: list[_Job]) -> tuple[list[str], list[str]]:
    valid, texts = [], []
    for j in jobs:
        t = ", ".join(sk.name for sk in j.required_skills)
        if t:
            valid.append(j); texts.append(f"{j.title}. {t}")
    if not valid:
        return [], []
    all_texts = [_student_text(student)] + texts
    embs = _encode(all_texts)
    s_emb, j_embs = embs[0], embs[1:]
    s_n = s_emb / (np.linalg.norm(s_emb) + 1e-9)
    j_n = j_embs / (np.linalg.norm(j_embs, axis=1, keepdims=True) + 1e-9)
    sims = j_n @ s_n
    K = min(30, len(valid))
    have = {s.name.lower() for s in student.skills}
    weight: dict[str, float] = defaultdict(float)
    count:  dict[str, int]   = defaultdict(int)
    for i in sims.argsort()[::-1][:K]:
        for sk in valid[i].required_skills:
            if sk.name.lower() not in have:
                weight[sk.name] += float(sims[i]); count[sk.name] += 1
    ss = sorted(weight.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ss[:5]], [n for n, _ in ss[:6]]


def _rag(student: _Student, jobs: list[_Job]) -> tuple[list[str], list[str]]:
    valid, texts = [], []
    for j in jobs:
        t = ", ".join(sk.name for sk in j.required_skills)
        if t:
            valid.append(j); texts.append(f"{j.title}. {t}")
    if not valid:
        return [], []
    all_texts = [_student_text(student)] + texts
    embs = _encode(all_texts)
    q_emb, j_embs = embs[0], embs[1:]
    q_n = q_emb / (np.linalg.norm(q_emb) + 1e-9)
    j_n = j_embs / (np.linalg.norm(j_embs, axis=1, keepdims=True) + 1e-9)
    scores = j_n @ q_n
    # Retrieve top 60 %, capped at 25
    K = min(max(int(len(valid) * 0.6), 12), 25)
    retrieved = [valid[i] for i in scores.argsort()[::-1][:K]]
    have = {s.name.lower() for s in student.skills}
    s2j: dict[str, set] = defaultdict(set)
    for j in retrieved:
        for sk in j.required_skills:
            if sk.name.lower() not in have:
                s2j[sk.name].add(id(j))
    if not s2j:
        return [], []
    ss = sorted(s2j.items(), key=lambda x: len(x[1]), reverse=True)
    path, covered, rem = [], set(), dict(ss)
    while rem and len(path) < 6:
        best = max(rem, key=lambda s: len(rem[s] - covered))
        if not (rem[best] - covered): break
        path.append(best); covered |= rem[best]; del rem[best]
    return [n for n, _ in ss[:5]], path


def _cf(student: _Student, _jobs: list[_Job]) -> tuple[list[str], list[str]]:
    all_skills_ordered = sorted({sk for v in COURSE_SKILL_PROFILES.values() for sk in v})
    skill_idx = {s: i for i, s in enumerate(all_skills_ordered)}
    n = len(all_skills_ordered)
    profiles = list(COURSE_SKILL_PROFILES.keys())
    matrix = np.zeros((len(profiles), n))
    for i, course in enumerate(profiles):
        for sk in COURSE_SKILL_PROFILES[course]:
            if sk in skill_idx:
                matrix[i, skill_idx[sk]] = 1.0
    have = {s.name.lower() for s in student.skills}
    sv = np.zeros(n)
    for sk, idx in skill_idx.items():
        if sk.lower() in have:
            sv[idx] = 1.0
    s_norm = np.linalg.norm(sv)
    if s_norm == 0:
        sims = np.ones(len(profiles)) / len(profiles)
    else:
        sv_n = sv / s_norm
        m_n  = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
        sims = m_n @ sv_n
    score: dict[str, float] = {}
    cnt:   dict[str, int]   = {}
    for i, course in enumerate(profiles):
        sim = float(sims[i])
        if sim <= 0: continue
        for sk in COURSE_SKILL_PROFILES[course]:
            if sk.lower() not in have:
                score[sk] = score.get(sk, 0.0) + sim
                cnt[sk]   = cnt.get(sk, 0) + 1
    if not score:
        return [], []
    ss = sorted(score.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ss[:5]], [n for n, _ in ss[:6]]


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _full_coverage(student: _Student, path: list[str], jobs: list[_Job]) -> float:
    have = {s.name.lower() for s in student.skills} | {s.lower() for s in path}
    return round(sum(1 for j in jobs if all(sk.name.lower() in have for sk in j.required_skills)) / len(jobs) * 100, 1)

def _domain_coverage(student: _Student, path: list[str], jobs: list[_Job]) -> float:
    dj = [j for j in jobs if j.domain == student.course]
    if not dj: return 0.0
    have = {s.name.lower() for s in student.skills} | {s.lower() for s in path}
    return round(sum(1 for j in dj if all(sk.name.lower() in have for sk in j.required_skills)) / len(dj) * 100, 1)

def _domain_precision(student: _Student, top5: list[str]) -> float:
    if not top5: return 0.0
    ds = {s.lower() for s in DOMAIN_SKILLS.get(student.course, set())}
    return round(sum(1 for s in top5 if s.lower() in ds) / len(top5) * 100, 1)


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

APPROACHES: dict[str, callable] = {
    "Greedy Set Cover":      _greedy,
    "GISMABERT Semantic":    _semantic,
    "RAG-Inspired":          _rag,
    "Collaborative Filter":  _cf,
}

W = 100

def run():
    print(f"\n{'='*W}")
    print("  GISMA Career Connect — Skill Gap Approach Comparison")
    print(f"  Corpus: {len(ALL_JOBS)} jobs  |  Students: {len(TEST_STUDENTS)}  |  Approaches: {len(APPROACHES)}")
    print(f"{'='*W}\n")

    agg: dict[str, dict] = {a: {"dp":[], "fc":[], "dc":[], "ms":[]} for a in APPROACHES}

    for student in TEST_STUDENTS:
        print(f"  Student : {student.label}")
        print(f"  Course  : {student.course}")
        print(f"  Skills  : {', '.join(s.name for s in student.skills) or '(none — cold-start test)'}")
        print(f"  {'─'*96}")
        print(f"  {'Approach':<24} {'Top-5 Missing Skills':<42} {'Dom%':>5} {'Full%':>6} {'DomCov%':>8} {'ms':>6}")
        print(f"  {'─'*96}")

        for name, fn in APPROACHES.items():
            t0 = time.perf_counter()
            top5, path = fn(student, ALL_JOBS)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            dp = _domain_precision(student, top5)
            fc = _full_coverage(student, path, ALL_JOBS)
            dc = _domain_coverage(student, path, ALL_JOBS)
            agg[name]["dp"].append(dp); agg[name]["fc"].append(fc)
            agg[name]["dc"].append(dc); agg[name]["ms"].append(ms)
            s_str = textwrap.shorten(", ".join(top5) if top5 else "—", 41, placeholder="…")
            print(f"  {name:<24} {s_str:<42} {dp:>4}% {fc:>5}% {dc:>7}% {ms:>5}")

        print()

    print(f"\n{'='*W}")
    print("  SUMMARY — Averages across all student profiles (excl. cold-start)")
    print(f"{'='*W}")
    print(f"  {'Approach':<24} {'Avg Dom.Precision':>19} {'Avg Full.Cov':>13} {'Avg Dom.Cov':>12} {'Avg ms':>8}")
    print(f"  {'─'*80}")

    # Exclude cold-start student (index 4) from averages
    for name, v in agg.items():
        dp_vals = v["dp"][:-1]; fc_vals = v["fc"][:-1]
        dc_vals = v["dc"][:-1]; ms_vals = v["ms"][:-1]
        adp = round(sum(dp_vals) / len(dp_vals), 1)
        afc = round(sum(fc_vals) / len(fc_vals), 1)
        adc = round(sum(dc_vals) / len(dc_vals), 1)
        ams = round(sum(ms_vals) / len(ms_vals), 1)
        print(f"  {name:<24} {adp:>18}% {afc:>12}% {adc:>11}% {ams:>7}")

    print(f"  {'─'*80}")
    print()
    print("  Metrics:")
    print("    Dom.Precision — % of suggested skills in the student's own domain")
    print("    Full.Cov      — % of all 36 jobs the 6-skill learning path unlocks")
    print("    Dom.Cov       — % of domain-specific jobs the learning path unlocks")
    print("    ms            — wall-clock response time (milliseconds)")
    print()
    print("  Cold-start (no skills): check which approaches still return useful results.")
    print()


if __name__ == "__main__":
    run()
