"""
STEP 1 — Collect job descriptions for GISMABert training using JobSpy.

JobSpy scrapes LinkedIn, Indeed, and Glassdoor in one call.
No API key needed. Works out of the box.

Install:
    pip install python-jobspy --break-system-packages

Run from python-backend/ folder:
    python collect_data.py

Takes ~15-25 minutes. Collects ~500-1000 job descriptions.
"""

import json
import time
import os

os.makedirs("data", exist_ok=True)

# ── GISMA courses → search terms ──────────────────────────────────────────────
# One focused search term per course — short, natural job titles that
# LinkedIn/Indeed understand well.
COURSE_QUERIES = {
    "Computer Science": [
        "Software Developer", "Python Developer", "Backend Developer",
        "Full Stack Developer", "Software Engineer",
    ],
    "Data Science & Analytics": [
        "Data Scientist", "Data Analyst", "Machine Learning Engineer",
        "Business Intelligence Analyst", "Data Engineer",
    ],
    "Business Administration": [
        "Business Analyst", "Management Consultant", "Operations Manager",
        "Business Development Manager",
    ],
    "International Management": [
        "International Business Manager", "Global Operations Manager",
        "Supply Chain Manager", "Trade Manager",
    ],
    "Marketing Management": [
        "Marketing Manager", "Digital Marketing Manager",
        "Social Media Manager", "Content Marketing Manager",
    ],
    "Finance & Accounting": [
        "Financial Analyst", "Finance Manager", "Accountant",
        "Controller", "Investment Analyst",
    ],
    "Digital Business": [
        "Product Manager", "UX Designer", "E-commerce Manager",
        "Digital Product Owner",
    ],
    "Project Management": [
        "Project Manager", "Scrum Master", "Agile Project Manager",
        "IT Project Manager",
    ],
    "Human Resource Management": [
        "HR Manager", "Recruiter", "Talent Acquisition Specialist",
        "HR Business Partner",
    ],
}


def fetch_with_jobspy(search_term: str, results: int = 30) -> list[dict]:
    """
    Scrape jobs via JobSpy (LinkedIn + Indeed).
    Returns a list of dicts with title, company, description fields.
    """
    try:
        from jobspy import scrape_jobs
        df = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=search_term,
            location="Germany",
            results_wanted=results,
            hours_old=72 * 30,     # last 30 days
            country_indeed="germany",
            verbose=0,
        )
        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            description = str(row.get("description") or "").strip()
            title       = str(row.get("title") or "").strip()
            company     = str(row.get("company") or "").strip()
            job_id      = str(row.get("id") or row.get("job_url") or f"{title}_{company}").strip()

            if not description or len(description) < 80:
                continue

            jobs.append({
                "id":          job_id,
                "title":       title,
                "company":     company,
                "description": description[:800],
                "source":      str(row.get("site") or "jobspy"),
            })
        return jobs

    except ImportError:
        print("\n❌ JobSpy not installed.")
        print("   Run: pip install python-jobspy --break-system-packages\n")
        raise
    except Exception as e:
        print(f"  ⚠️  JobSpy error: {e}")
        return []


def main():
    all_jobs  = []
    seen_ids  = set()

    print("🔍 Collecting jobs via JobSpy (LinkedIn + Indeed — Germany)...\n")

    for course, queries in COURSE_QUERIES.items():
        print(f"📚 Course: {course}")
        course_count = 0

        for query in queries:
            print(f"   '{query}'...", end=" ", flush=True)
            raw = fetch_with_jobspy(query, results=30)
            added = 0

            for job in raw:
                uid = job["id"]
                if uid in seen_ids:
                    continue
                seen_ids.add(uid)
                job["course"] = course
                job["query"]  = query
                all_jobs.append(job)
                added += 1

            print(f"{added} jobs")
            # Pause between requests to avoid rate limiting
            time.sleep(4)

        print(f"   ✅ {course_count} unique jobs for this course\n")

    # Save
    output_path = "data/raw_jobs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    print(f"{'─'*50}")
    print(f"✅ Done! {len(all_jobs)} unique job descriptions saved.")
    print(f"📁 Saved to: {output_path}")

    print(f"\nBreakdown by course:")
    for course in COURSE_QUERIES:
        count = sum(1 for j in all_jobs if j["course"] == course)
        bar   = "█" * (count // 5)
        print(f"  {course:<35} {count:>4}  {bar}")

    print(f"\nNext step: python generate_pairs.py")


if __name__ == "__main__":
    main()
