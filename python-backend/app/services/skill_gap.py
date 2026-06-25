from __future__ import annotations
from collections import defaultdict

from ..models import Job, Student
from ..schemas import SkillGapItem, SkillGapResponse


def analyse(student: Student, jobs: list[Job]) -> SkillGapResponse:
    student_set = {s.name.lower() for s in student.skills}

    skill_to_jobs: dict[str, set[int]] = defaultdict(set)

    for job in jobs:
        for skill in job.required_skills:
            if skill.name.lower() not in student_set:
                skill_to_jobs[skill.name].add(job.id)

    if not skill_to_jobs:
        return SkillGapResponse(top_missing=[], learning_path=[])

    sorted_skills = sorted(skill_to_jobs.items(), key=lambda x: len(x[1]), reverse=True)

    top_missing = [
        SkillGapItem(skill=name, unlocks_jobs=len(job_ids))
        for name, job_ids in sorted_skills[:8]
    ]

    # Greedy set-cover: pick skill that unlocks the most new jobs each step
    learning_path: list[str] = []
    covered_jobs: set[int] = set()
    remaining = dict(sorted_skills)

    while remaining and len(learning_path) < 6:
        best_skill = max(remaining, key=lambda s: len(remaining[s] - covered_jobs))
        new_jobs   = remaining[best_skill] - covered_jobs

        if not new_jobs:
            break

        learning_path.append(best_skill)
        covered_jobs |= remaining[best_skill]
        del remaining[best_skill]

    return SkillGapResponse(top_missing=top_missing, learning_path=learning_path)
