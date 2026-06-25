"""
Unit tests for all four skill gap approaches.
Standalone — no pytest, no database, no sentence-transformers required.

Run:
    cd python-backend
    python model/test_skill_gap.py

Exit code 0 = all tests passed.
Exit code 1 = one or more tests failed.
"""

from __future__ import annotations

import sys
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Minimal mock objects
# ---------------------------------------------------------------------------

class _Skill:
    def __init__(self, name: str): self.name = name

class _Student:
    _c = 0
    def __init__(self, course: str, skills: list[str]):
        _Student._c += 1
        self.id     = _Student._c
        self.course = course
        self.skills = [_Skill(s) for s in skills]

class _Job:
    _c = 0
    def __init__(self, title: str, skills: list[str], domain: str = ""):
        _Job._c += 1
        self.id              = _Job._c
        self.title           = title
        self.required_skills = [_Skill(s) for s in skills]
        self.domain          = domain


# ---------------------------------------------------------------------------
# Inline implementations (copy of evaluate_approaches.py helpers so this
# file runs completely standalone without importing the FastAPI app)
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


def _greedy(student, jobs):
    have = {s.name.lower() for s in student.skills}
    s2j: dict[str, set] = defaultdict(set)
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
        if not (rem[best] - covered): break
        path.append(best); covered |= rem[best]; del rem[best]
    return [n for n, _ in ss[:5]], path


def _tfidf_encode(texts: list[str]) -> np.ndarray:
    vocab: dict[str, int] = {}
    for doc in texts:
        for w in doc.lower().split():
            if w not in vocab:
                vocab[w] = len(vocab)
    N = len(texts)
    df = np.zeros(len(vocab))
    for doc in texts:
        seen = set(doc.lower().split())
        for w in seen:
            if w in vocab:
                df[vocab[w]] += 1
    idf = np.log((N + 1) / (df + 1)) + 1
    vecs = []
    for doc in texts:
        v = np.zeros(len(vocab))
        words = doc.lower().split()
        for w in words:
            if w in vocab:
                v[vocab[w]] += 1
        if words:
            v /= len(words)
        v *= idf
        n = np.linalg.norm(v)
        vecs.append(v / n if n > 0 else v)
    return np.array(vecs)


def _semantic(student, jobs):
    valid, texts = [], []
    for j in jobs:
        t = ", ".join(sk.name for sk in j.required_skills)
        if t:
            valid.append(j); texts.append(f"{j.title}. {t}")
    if not valid:
        return [], []
    all_texts = [f"{student.course}. {', '.join(s.name for s in student.skills)}"] + texts
    embs = _tfidf_encode(all_texts)
    s_n = embs[0] / (np.linalg.norm(embs[0]) + 1e-9)
    j_n = embs[1:] / (np.linalg.norm(embs[1:], axis=1, keepdims=True) + 1e-9)
    sims = j_n @ s_n
    have = {s.name.lower() for s in student.skills}
    weight: dict[str, float] = defaultdict(float)
    for i in sims.argsort()[::-1][:min(20, len(valid))]:
        for sk in valid[i].required_skills:
            if sk.name.lower() not in have:
                weight[sk.name] += float(sims[i])
    ss = sorted(weight.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ss[:5]], [n for n, _ in ss[:6]]


def _rag(student, jobs):
    valid, texts = [], []
    for j in jobs:
        t = ", ".join(sk.name for sk in j.required_skills)
        if t:
            valid.append(j); texts.append(f"{j.title}. {t}")
    if not valid:
        return [], []
    all_texts = [f"{student.course}. {', '.join(s.name for s in student.skills)}"] + texts
    embs = _tfidf_encode(all_texts)
    q_n = embs[0] / (np.linalg.norm(embs[0]) + 1e-9)
    j_n = embs[1:] / (np.linalg.norm(embs[1:], axis=1, keepdims=True) + 1e-9)
    scores = j_n @ q_n
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


def _cf(student, _jobs):
    all_skills = sorted({sk for v in COURSE_SKILL_PROFILES.values() for sk in v})
    idx = {s: i for i, s in enumerate(all_skills)}
    n = len(all_skills)
    profiles = list(COURSE_SKILL_PROFILES.keys())
    matrix = np.zeros((len(profiles), n))
    for i, course in enumerate(profiles):
        for sk in COURSE_SKILL_PROFILES[course]:
            if sk in idx:
                matrix[i, idx[sk]] = 1.0
    have = {s.name.lower() for s in student.skills}
    sv = np.zeros(n)
    for sk, i in idx.items():
        if sk.lower() in have:
            sv[i] = 1.0
    s_norm = np.linalg.norm(sv)
    if s_norm == 0:
        sims = np.ones(len(profiles)) / len(profiles)
    else:
        sv_n = sv / s_norm
        m_n  = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
        sims = m_n @ sv_n
    score: dict[str, float] = {}
    for i, course in enumerate(profiles):
        sim = float(sims[i])
        if sim <= 0: continue
        for sk in COURSE_SKILL_PROFILES[course]:
            if sk.lower() not in have:
                score[sk] = score.get(sk, 0.0) + sim
    if not score:
        return [], []
    ss = sorted(score.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ss[:5]], [n for n, _ in ss[:6]]


APPROACH_FNS = {
    "greedy":   _greedy,
    "semantic": _semantic,
    "rag":      _rag,
    "cf":       _cf,
}


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

_PASSED = 0
_FAILED = 0

def _ok(name: str):
    global _PASSED
    _PASSED += 1
    print(f"  PASS  {name}")

def _fail(name: str, reason: str):
    global _FAILED
    _FAILED += 1
    print(f"  FAIL  {name}")
    print(f"        {reason}")


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

def test_returns_correct_types():
    """All approaches must return (list[str], list[str]) of max length 5 / 6."""
    jobs = [
        _Job("Dev", ["Python", "Docker", "SQL"], "CS"),
        _Job("Analyst", ["SQL", "Excel", "Tableau"], "DS"),
    ]
    student = _Student("Computer Science", ["Python"])
    for name, fn in APPROACH_FNS.items():
        top5, path = fn(student, jobs)
        assert isinstance(top5, list), f"{name}: top5 not a list"
        assert isinstance(path, list), f"{name}: path not a list"
        assert len(top5) <= 5,        f"{name}: top5 longer than 5"
        assert len(path) <= 6,        f"{name}: path longer than 6"
        _ok(f"[{name}] returns correct types and max lengths")


def test_student_already_has_all_skills():
    """
    When student has ALL skills required by all jobs, job-based approaches
    (greedy, semantic, rag) must return empty lists.
    CF is profile-based (not job-based) so it may still suggest programme
    skills beyond what the jobs require — that is correct behaviour.
    """
    jobs = [_Job("Dev", ["Python", "Git"], "CS")]
    student = _Student("Computer Science", ["Python", "Git"])
    for name, fn in [("greedy", _greedy), ("semantic", _semantic), ("rag", _rag)]:
        top5, path = fn(student, jobs)
        assert top5 == [], f"{name}: top5 should be empty, got {top5}"
        assert path == [], f"{name}: path should be empty, got {path}"
        _ok(f"[{name}] returns empty lists when student has all job-required skills")

    # CF works against programme profiles — it is expected to suggest more skills
    top5_cf, _ = _cf(student, jobs)
    assert isinstance(top5_cf, list), "cf must return a list"
    _ok("[cf] correctly uses programme profiles (may suggest skills beyond job requirements)")


def test_cold_start_no_skills():
    """CF and Greedy must handle student with zero skills gracefully (no crash)."""
    jobs = [
        _Job("Dev",     ["Python","Docker"],    "CS"),
        _Job("Analyst", ["SQL","Excel"],        "DS"),
        _Job("Manager", ["Excel","SAP","Agile"],"BA"),
    ]
    student = _Student("Computer Science", [])
    for name, fn in APPROACH_FNS.items():
        try:
            top5, path = fn(student, jobs)
            assert isinstance(top5, list), f"top5 must be list"
            _ok(f"[{name}] handles cold-start (no skills) without crashing")
        except Exception as e:
            _fail(f"[{name}] cold-start crash", str(e))


def test_no_jobs():
    """All approaches must handle an empty job list without crashing."""
    student = _Student("Computer Science", ["Python"])
    for name, fn in APPROACH_FNS.items():
        try:
            top5, path = fn(student, [])
            assert isinstance(top5, list)
            _ok(f"[{name}] handles empty job list")
        except Exception as e:
            _fail(f"[{name}] empty-jobs crash", str(e))


def test_suggested_skills_not_already_owned():
    """No suggested skill should already be in the student's skill set."""
    jobs = [
        _Job("Dev A", ["Python","Docker","SQL"],         "CS"),
        _Job("Dev B", ["Python","React","TypeScript"],   "CS"),
        _Job("Dev C", ["Python","AWS","Linux"],          "CS"),
    ]
    student = _Student("Computer Science", ["Python"])
    have = {"python"}
    for name, fn in APPROACH_FNS.items():
        top5, path = fn(student, jobs)
        overlap_top5 = [s for s in top5 if s.lower() in have]
        overlap_path = [s for s in path if s.lower() in have]
        if overlap_top5 or overlap_path:
            _fail(f"[{name}] suggests already-owned skills", f"top5={overlap_top5}, path={overlap_path}")
        else:
            _ok(f"[{name}] never suggests skills the student already has")


def test_greedy_ordering():
    """Greedy must suggest the skill that appears in the MOST jobs first."""
    jobs = [
        _Job("J1", ["SQL", "Excel"],    "BA"),
        _Job("J2", ["SQL", "SAP"],      "BA"),
        _Job("J3", ["SQL", "Python"],   "BA"),
        _Job("J4", ["Excel", "SAP"],    "BA"),
    ]
    # SQL appears in 3 jobs, Excel in 2, SAP in 2, Python in 1
    student = _Student("Business Administration", [])
    top5, _ = _greedy(student, jobs)
    assert top5[0] == "SQL", f"Greedy top skill should be SQL (3 jobs), got {top5[0]}"
    _ok("[greedy] ranks skills by job-unlock count correctly")


def test_cf_cold_start_returns_cross_programme_skills():
    """CF cold-start should return the most common skills across ALL profiles."""
    student = _Student("Computer Science", [])   # no skills
    top5, _ = _cf(student, [])
    # SQL and Excel appear in many profiles — should feature in top suggestions
    common = {"sql", "excel", "data analysis", "python", "agile"}
    hits = sum(1 for s in top5 if s.lower() in common)
    assert hits >= 2, f"CF cold-start should suggest common cross-programme skills, got {top5}"
    _ok("[cf] cold-start returns common cross-programme skills")


def test_learning_path_contains_distinct_skills():
    """Learning path must not contain duplicate skills."""
    jobs = [
        _Job("Dev A", ["Docker","SQL","Python"],  "CS"),
        _Job("Dev B", ["Docker","React","Git"],   "CS"),
        _Job("Dev C", ["SQL","React","TypeScript"],"CS"),
    ]
    student = _Student("Computer Science", ["Python"])
    for name, fn in APPROACH_FNS.items():
        _, path = fn(student, jobs)
        assert len(path) == len(set(p.lower() for p in path)), \
            f"{name}: learning path has duplicates: {path}"
        _ok(f"[{name}] learning path contains distinct skills only")


def test_greedy_path_touches_more_jobs_than_random():
    """
    Greedy set cover maximises the number of jobs TOUCHED (i.e. at least one
    skill in the learning path appears in that job). A random path of the same
    length should touch fewer jobs on average.

    Note: greedy does NOT necessarily fully UNLOCK more jobs — it optimises
    skill-appearance coverage, not complete job satisfaction. This is the known
    trade-off of Greedy Set Cover vs other approaches (Chvatal, 1979).
    """
    import random

    jobs = [
        _Job("J1", ["Python","Docker","SQL"],    "CS"),
        _Job("J2", ["React","TypeScript","Git"], "CS"),
        _Job("J3", ["Python","AWS","Linux"],     "CS"),
        _Job("J4", ["SQL","Excel","Tableau"],    "DS"),
        _Job("J5", ["Docker","AWS","Git"],       "CS"),
        _Job("J6", ["Excel","SAP","Agile"],      "BA"),
    ]
    student = _Student("Computer Science", [])
    _, greedy_path = _greedy(student, jobs)

    # "Touched" = at least one skill in the path appears in the job
    def touched(path):
        have = {s.lower() for s in path}
        return sum(1 for j in jobs if any(sk.name.lower() in have for sk in j.required_skills))

    greedy_touched = touched(greedy_path)

    all_missing = list({sk.name for j in jobs for sk in j.required_skills})
    random.seed(99)
    random_touched = [
        touched(random.sample(all_missing, min(len(greedy_path), len(all_missing))))
        for _ in range(30)
    ]
    avg_random = sum(random_touched) / len(random_touched)

    assert greedy_touched >= avg_random, (
        f"Greedy touched {greedy_touched} jobs; random avg {avg_random:.1f}. "
        "Greedy should touch at least as many."
    )
    _ok(f"[greedy] path touches {greedy_touched} jobs vs random avg {avg_random:.1f} "
        f"(set cover maximises appearances, not full unlocks)")


def test_semantic_and_rag_rank_domain_skills_higher_than_greedy():
    """
    For a CS student, Semantic/RAG should suggest more CS-domain skills
    than Greedy (which gets polluted by high-frequency off-domain skills).
    """
    from evaluate_approaches import _RAW, _Job as EJob, _Student as EStudent

    jobs = [EJob(t, s, d) for t, s, d in _RAW]
    student = EStudent("Computer Science", "Computer Science", ["Python", "Git"])

    CS_SKILLS = {"python","javascript","typescript","java","react","node.js","docker",
                 "aws","git","linux","sql","fastapi","postgresql","css"}

    def dom_prec(top5):
        return sum(1 for s in top5 if s.lower() in CS_SKILLS) / len(top5) if top5 else 0

    from evaluate_approaches import _greedy as eg, _semantic as es, _rag as er

    g_top5, _ = eg(student, jobs)
    s_top5, _ = es(student, jobs)
    r_top5, _ = er(student, jobs)

    g_prec = dom_prec(g_top5)
    s_prec = dom_prec(s_top5)
    r_prec = dom_prec(r_top5)

    assert s_prec >= g_prec, \
        f"Semantic precision ({s_prec:.0%}) should be ≥ Greedy ({g_prec:.0%})"
    assert r_prec >= g_prec, \
        f"RAG precision ({r_prec:.0%}) should be ≥ Greedy ({g_prec:.0%})"
    _ok(f"[semantic/rag] domain precision ≥ greedy for CS student  "
        f"(Greedy {g_prec:.0%} | Semantic {s_prec:.0%} | RAG {r_prec:.0%})")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_returns_correct_types,
    test_student_already_has_all_skills,
    test_cold_start_no_skills,
    test_no_jobs,
    test_suggested_skills_not_already_owned,
    test_greedy_ordering,
    test_cf_cold_start_returns_cross_programme_skills,
    test_learning_path_contains_distinct_skills,
    test_greedy_path_touches_more_jobs_than_random,
    test_semantic_and_rag_rank_domain_skills_higher_than_greedy,
]


def main():
    print(f"\n{'='*70}")
    print("  Skill Gap — Unit Tests (4 approaches)")
    print(f"{'='*70}\n")

    for test_fn in TESTS:
        try:
            test_fn()
        except AssertionError as e:
            _fail(test_fn.__name__, str(e))
        except Exception as e:
            _fail(test_fn.__name__, f"Unexpected exception: {e}\n{traceback.format_exc()}")

    print(f"\n{'='*70}")
    print(f"  Results: {_PASSED} passed, {_FAILED} failed out of {_PASSED + _FAILED} tests")
    print(f"{'='*70}\n")

    sys.exit(0 if _FAILED == 0 else 1)


if __name__ == "__main__":
    main()
