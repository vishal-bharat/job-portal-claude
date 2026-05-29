from sqlalchemy import Column, Integer, String, Date, Table, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-many: students <-> skills
student_skills = Table(
    "student_skills", Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("skill_id",   Integer, ForeignKey("skills.id"),   primary_key=True),
)

# Many-to-many: jobs <-> skills
job_skills = Table(
    "job_skills", Base.metadata,
    Column("job_id",   Integer, ForeignKey("jobs.id"),   primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class Student(Base):
    __tablename__ = "students"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, nullable=False, index=True)
    password   = Column(String, nullable=False)
    name       = Column(String, nullable=False)
    university = Column(String)
    course     = Column(String)
    year       = Column(Integer)

    skills = relationship("Skill", secondary=student_skills, lazy="joined")


class Job(Base):
    __tablename__ = "jobs"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, nullable=False)
    company     = Column(String, nullable=False)
    location    = Column(String)
    job_type    = Column(String)   # internship | fulltime | parttime | remote
    salary      = Column(String)
    posted_date = Column(Date)

    required_skills = relationship("Skill", secondary=job_skills, lazy="joined")
