-- ============================================================
-- GISMA Career Connect - Seed data
-- Idempotent: re-running won't duplicate rows.
-- Demo user: alex@gisma.edu  /  password123
-- ============================================================

-- Skills catalog ---------------------------------------------------
INSERT INTO skills (name) VALUES ('Python')        ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('JavaScript')    ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('React')         ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('SQL')           ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Machine Learning') ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Figma')         ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('TypeScript')    ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Docker')        ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('AWS')           ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('UI/UX')         ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Data Analysis') ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Java')          ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Node.js')       ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Kubernetes')    ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Pandas')        ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Tableau')       ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Excel')         ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('REST APIs')     ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('Spring Boot')   ON CONFLICT (name) DO NOTHING;
INSERT INTO skills (name) VALUES ('PostgreSQL')    ON CONFLICT (name) DO NOTHING;

-- Demo student: alex@gisma.edu / password123 ----------------------
INSERT INTO students (email, password, name, university, course, year)
VALUES ('alex@gisma.edu',
        '$2b$10$uwPR4WN02EIlUjE1GbL/xeuFEtkMXWZXPq23R9O1wbqCYnez/1MF6',
        'Alex Student',
        'GISMA University of Applied Sciences',
        'Computer Science',
        3)
ON CONFLICT (email) DO NOTHING;

-- Default skills for Alex (Python, JavaScript, SQL, Data Analysis)
INSERT INTO student_skills (student_id, skill_id)
SELECT s.id, k.id FROM students s, skills k
WHERE s.email='alex@gisma.edu' AND k.name IN ('Python','JavaScript','SQL','Data Analysis')
ON CONFLICT DO NOTHING;

-- Jobs -----------------------------------------------------------
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Data Science Intern', 'Siemens', 'Munich', 'internship', '€1,000/mo', CURRENT_DATE - 1)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Data Analyst Intern', 'HelloFresh', 'Berlin', 'internship', '€900/mo', CURRENT_DATE - 6)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Backend Engineer', 'Delivery Hero', 'Berlin', 'fulltime', '€55,000-75,000', CURRENT_DATE - 5)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Frontend Developer', 'Zalando', 'Berlin', 'fulltime', '€50,000-65,000', CURRENT_DATE - 3)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('ML Engineer Intern', 'BMW Group', 'Munich', 'internship', '€1,200/mo', CURRENT_DATE - 2)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Product Designer', 'N26', 'Berlin', 'fulltime', '€45,000-60,000', CURRENT_DATE - 4)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Full Stack Developer', 'Trivago', 'Remote', 'remote', '€55,000-70,000', CURRENT_DATE - 7)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Cloud Engineer', 'SAP', 'Walldorf', 'fulltime', '€60,000-80,000', CURRENT_DATE - 10)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('UX Researcher', 'Booking.com', 'Amsterdam', 'parttime', '€25/h', CURRENT_DATE - 8)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('DevOps Intern', 'Spotify', 'Stockholm', 'internship', '€1,100/mo', CURRENT_DATE - 1)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('Business Analyst', 'About You', 'Hamburg', 'fulltime', '€48,000-58,000', CURRENT_DATE - 9)
ON CONFLICT DO NOTHING;
INSERT INTO jobs (title, company, location, job_type, salary, posted_date)
VALUES ('React Native Developer', 'Flink', 'Remote', 'remote', '€52,000-68,000', CURRENT_DATE - 2)
ON CONFLICT DO NOTHING;

-- Job <-> required skills (each block: clear, then insert) --------
-- Data Science Intern: Python, Machine Learning, SQL, Data Analysis, Pandas
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Data Science Intern' AND j.company='Siemens'
  AND k.name IN ('Python','Machine Learning','SQL','Data Analysis','Pandas')
ON CONFLICT DO NOTHING;

-- Data Analyst Intern: SQL, Python, Tableau, Data Analysis, Excel
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Data Analyst Intern' AND j.company='HelloFresh'
  AND k.name IN ('SQL','Python','Tableau','Data Analysis','Excel')
ON CONFLICT DO NOTHING;

-- Backend Engineer: Python, Java, Docker, Kubernetes, SQL, REST APIs
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Backend Engineer' AND j.company='Delivery Hero'
  AND k.name IN ('Python','Java','Docker','Kubernetes','SQL','REST APIs')
ON CONFLICT DO NOTHING;

-- Frontend Developer: JavaScript, TypeScript, React, UI/UX
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Frontend Developer' AND j.company='Zalando'
  AND k.name IN ('JavaScript','TypeScript','React','UI/UX')
ON CONFLICT DO NOTHING;

-- ML Engineer Intern: Python, Machine Learning, AWS, Docker
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='ML Engineer Intern' AND j.company='BMW Group'
  AND k.name IN ('Python','Machine Learning','AWS','Docker')
ON CONFLICT DO NOTHING;

-- Product Designer: Figma, UI/UX
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Product Designer' AND j.company='N26'
  AND k.name IN ('Figma','UI/UX')
ON CONFLICT DO NOTHING;

-- Full Stack Developer: JavaScript, React, Node.js, SQL, REST APIs
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Full Stack Developer' AND j.company='Trivago'
  AND k.name IN ('JavaScript','React','Node.js','SQL','REST APIs')
ON CONFLICT DO NOTHING;

-- Cloud Engineer: AWS, Docker, Kubernetes, Java
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Cloud Engineer' AND j.company='SAP'
  AND k.name IN ('AWS','Docker','Kubernetes','Java')
ON CONFLICT DO NOTHING;

-- UX Researcher: UI/UX, Figma
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='UX Researcher' AND j.company='Booking.com'
  AND k.name IN ('UI/UX','Figma')
ON CONFLICT DO NOTHING;

-- DevOps Intern: Docker, Kubernetes, AWS, Python
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='DevOps Intern' AND j.company='Spotify'
  AND k.name IN ('Docker','Kubernetes','AWS','Python')
ON CONFLICT DO NOTHING;

-- Business Analyst: SQL, Excel, Tableau, Data Analysis
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='Business Analyst' AND j.company='About You'
  AND k.name IN ('SQL','Excel','Tableau','Data Analysis')
ON CONFLICT DO NOTHING;

-- React Native Developer: JavaScript, TypeScript, React
INSERT INTO job_skills (job_id, skill_id)
SELECT j.id, k.id FROM jobs j, skills k
WHERE j.title='React Native Developer' AND j.company='Flink'
  AND k.name IN ('JavaScript','TypeScript','React')
ON CONFLICT DO NOTHING;
