from .database import SessionLocal, engine, Base
from .models import Job, Skill

Base.metadata.create_all(bind=engine)

SEED_JOBS = [
    # Computer Science
    {"title": "Backend Python Developer",       "company": "TechHub Berlin",       "location": "Berlin",    "job_type": "fulltime",   "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"]},
    {"title": "Full Stack Developer",           "company": "Zalando",              "location": "Berlin",    "job_type": "fulltime",   "skills": ["React", "Node.js", "TypeScript", "SQL", "Git"]},
    {"title": "Software Engineer Intern",       "company": "SAP",                  "location": "Potsdam",   "job_type": "internship", "skills": ["Java", "SQL", "Git", "Agile"]},
    {"title": "DevOps Engineer",                "company": "Siemens",              "location": "Munich",    "job_type": "fulltime",   "skills": ["Docker", "AWS", "Git", "Python", "Linux"]},
    {"title": "Frontend Developer",             "company": "Delivery Hero",        "location": "Berlin",    "job_type": "fulltime",   "skills": ["React", "JavaScript", "TypeScript", "CSS", "Git"]},
    {"title": "Cloud Engineer",                 "company": "Deutsche Telekom",     "location": "Bonn",      "job_type": "fulltime",   "skills": ["AWS", "Docker", "Python", "Linux", "Git"]},
    {"title": "Mobile Developer (Android)",     "company": "N26",                  "location": "Berlin",    "job_type": "fulltime",   "skills": ["Java", "Git", "SQL", "Agile"]},
    {"title": "Junior Software Developer",      "company": "Check24",              "location": "Munich",    "job_type": "fulltime",   "skills": ["Python", "JavaScript", "SQL", "Git"]},

    # Data Science
    {"title": "Data Scientist",                 "company": "BMW Group",            "location": "Munich",    "job_type": "fulltime",   "skills": ["Python", "Machine Learning", "SQL", "Data Analysis", "Git"]},
    {"title": "Machine Learning Engineer",      "company": "Bosch",                "location": "Stuttgart", "job_type": "fulltime",   "skills": ["Python", "Machine Learning", "Docker", "SQL", "Git"]},
    {"title": "Data Analyst",                   "company": "Volkswagen",           "location": "Wolfsburg", "job_type": "fulltime",   "skills": ["SQL", "Python", "Excel", "Tableau", "Data Analysis"]},
    {"title": "BI Analyst",                     "company": "Metro AG",             "location": "Düsseldorf","job_type": "fulltime",   "skills": ["SQL", "Power BI", "Excel", "Data Analysis"]},
    {"title": "Data Engineer",                  "company": "Axel Springer",        "location": "Berlin",    "job_type": "fulltime",   "skills": ["Python", "SQL", "Docker", "AWS", "Git"]},
    {"title": "Data Science Intern",            "company": "Bayer",                "location": "Leverkusen","job_type": "internship", "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"]},
    {"title": "Analytics Engineer",             "company": "HelloFresh",           "location": "Berlin",    "job_type": "fulltime",   "skills": ["SQL", "Python", "Data Analysis", "Git"]},

    # Business
    {"title": "Business Analyst",               "company": "McKinsey & Company",   "location": "Frankfurt", "job_type": "fulltime",   "skills": ["Excel", "SQL", "Data Analysis", "Power BI", "Agile"]},
    {"title": "Management Consultant",          "company": "Deloitte",             "location": "Frankfurt", "job_type": "fulltime",   "skills": ["Excel", "Data Analysis", "Agile", "SAP"]},
    {"title": "Operations Manager",             "company": "DHL",                  "location": "Bonn",      "job_type": "fulltime",   "skills": ["Excel", "SAP", "Data Analysis", "Agile"]},
    {"title": "Strategy Analyst Intern",        "company": "BCG",                  "location": "Munich",    "job_type": "internship", "skills": ["Excel", "Data Analysis", "SQL"]},
    {"title": "Project Manager",                "company": "Deutsche Bahn",        "location": "Berlin",    "job_type": "fulltime",   "skills": ["Agile", "Excel", "SAP", "Data Analysis"]},

    # Finance
    {"title": "Financial Analyst",              "company": "Deutsche Bank",        "location": "Frankfurt", "job_type": "fulltime",   "skills": ["Excel", "SQL", "Data Analysis", "Power BI"]},
    {"title": "Investment Banking Analyst",     "company": "Goldman Sachs",        "location": "Frankfurt", "job_type": "fulltime",   "skills": ["Excel", "Data Analysis", "SQL"]},
    {"title": "Finance Intern",                 "company": "Allianz",              "location": "Munich",    "job_type": "internship", "skills": ["Excel", "SAP", "Data Analysis"]},
    {"title": "Risk Analyst",                   "company": "Commerzbank",          "location": "Frankfurt", "job_type": "fulltime",   "skills": ["SQL", "Excel", "Python", "Data Analysis"]},

    # Marketing
    {"title": "Digital Marketing Analyst",      "company": "Zalando",              "location": "Berlin",    "job_type": "fulltime",   "skills": ["Excel", "Data Analysis", "SQL", "Tableau"]},
    {"title": "Marketing Manager",              "company": "Henkel",               "location": "Düsseldorf","job_type": "fulltime",   "skills": ["Excel", "Data Analysis", "Agile"]},
    {"title": "Growth Marketing Intern",        "company": "Wolt",                 "location": "Berlin",    "job_type": "internship", "skills": ["Excel", "Data Analysis", "SQL"]},

    # UX/Product
    {"title": "UX Designer",                    "company": "Spotify",              "location": "Berlin",    "job_type": "fulltime",   "skills": ["Figma", "JavaScript", "Agile", "Git"]},
    {"title": "Product Manager",                "company": "Trivago",              "location": "Düsseldorf","job_type": "fulltime",   "skills": ["Agile", "SQL", "Data Analysis", "Figma"]},
    {"title": "Product Designer Intern",        "company": "SoundCloud",           "location": "Berlin",    "job_type": "internship", "skills": ["Figma", "Agile"]},

    # International
    {"title": "Supply Chain Analyst",           "company": "Adidas",               "location": "Herzogenaurach", "job_type": "fulltime", "skills": ["Excel", "SAP", "Data Analysis", "SQL"]},
    {"title": "Logistics Manager",              "company": "Rhenus Logistics",     "location": "Holzwickede",    "job_type": "fulltime", "skills": ["SAP", "Excel", "Data Analysis"]},
    {"title": "International Trade Analyst",    "company": "Siemens",              "location": "Munich",    "job_type": "fulltime",   "skills": ["Excel", "SAP", "Data Analysis", "SQL"]},

    # Remote
    {"title": "Remote Python Developer",        "company": "Personio",             "location": "Remote",    "job_type": "remote",     "skills": ["Python", "SQL", "Docker", "Git"]},
    {"title": "Part-time Data Analyst",         "company": "Statista",             "location": "Hamburg",   "job_type": "parttime",   "skills": ["SQL", "Excel", "Data Analysis", "Tableau"]},
    {"title": "Freelance Frontend Developer",   "company": "Xing",                 "location": "Remote",    "job_type": "remote",     "skills": ["React", "JavaScript", "TypeScript", "CSS"]},
]


def run():
    db = SessionLocal()
    try:
        added = 0
        for j in SEED_JOBS:
            exists = db.query(Job).filter(
                Job.title == j["title"],
                Job.company == j["company"]
            ).first()
            if exists:
                continue

            skill_objs = []
            for name in j["skills"]:
                skill = db.query(Skill).filter(Skill.name == name).first()
                if not skill:
                    skill = Skill(name=name)
                    db.add(skill)
                    db.flush()
                skill_objs.append(skill)

            job = Job(
                title=j["title"],
                company=j["company"],
                location=j.get("location"),
                job_type=j.get("job_type"),
                salary=None,
                posted_date=None,
                required_skills=skill_objs,
            )
            db.add(job)
            added += 1

        db.commit()
        print(f"Seeded {added} jobs ({len(SEED_JOBS) - added} already existed)")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
