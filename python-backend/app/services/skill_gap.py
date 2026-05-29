"""
Skill Gap Analysis service.

Answers the question: "What skills should I learn NEXT to get the most job matches?"

Algorithm:
──────────
1. Find every skill required by any job that the student doesn't have yet.
2. Count how many jobs each missing skill would unlock (i.e., appear in).
3. Sort by unlock count descending → top_missing list.
4. Build a learning_path: pick skills greedily so each step adds new jobs
   that weren't already covered by previously chosen skills.

This is a greedy set-cover approximation — the simplest approach that gives
a sensible learning priority order and is easy to explain to a professor.
"""

from __future__ import annotations
from collections import defaultdict

from ..models import Job, Student
from ..schemas import SkillGapItem, SkillGapResponse


def analyse(student: Student, jobs: list[Job]) -> SkillGapResponse:
    student_set = {s.name.lower() for s in student.skills}

    # Map: missing_skill → set of job ids it appears in
    skill_to_jobs: dict[str, set[int]] = defaultdict(set)

    for job in jobs:
        for skill in job.required_skills:
            if skill.name.lower() not in student_set:
                skill_to_jobs[skill.name].add(job.id)

    if not skill_to_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[])

    # Sort by number of jobs unlocked
    sorted_skills = sorted(skill_to_jobs.items(), key=lambda x: len(x[1]), reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=len(job_ids))
        for name, job_ids in sorted_skills[:8]
    ]

    # Greedy learning path: each step picks the skill that unlocks the most
    # NEW jobs not already covered by previously selected skills
    learning_path: list[str] = []
    covered_jobs: set[int] = set()

    remaining = dict(sorted_skills)

    while remaining and len(learning_path) < 6:
        # Recompute uncovered job count for each remaining skill
        best_skill = max(remaining, key=lambda s: len(remaining[s] - covered_jobs))
        new_jobs   = remaining[best_skill] - covered_jobs

        if not new_jobs:
            break  # No more new coverage possible

        learning_path.append(best_skill)
        covered_jobs |= remaining[best_skill]
        del remaining[best_skill]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path)
