# GISMA Career Connect

A simple job recommendation portal for university students.
Students log in, manage their skills, and the dashboard ranks open opportunities by skill-match percentage. Add or remove a skill and the matches update immediately.

**Stack** — Java 17 + Spring Boot 3 + PostgreSQL backend, React 18 (Vite) frontend.
**Architecture** — kept intentionally simple: one Spring Boot app, one Postgres database, one React SPA. No Redis, no message queues, no microservices.

---

## Features in this version

1. **Student Login** — JWT-based auth (`/api/auth/login`, `/api/auth/signup`).
2. **My Profile** — view & edit name, university, course, year, and skills.
3. **Home / Opportunities** — add or remove skills, filter by job type (All / Full-time / Internship / Remote / Part-time), see matched jobs ranked by match %, plus side panels for skill-job counts, trending roles and "boost matches" suggestions.

---

## Quick start (Docker — recommended)

Prereq: Docker Desktop (or any recent Docker engine with Compose v2).

From the project root:

```bash
docker compose up --build
```

That command builds three images and starts three containers:

| Container     | Image base                       | Host port | What it is               |
|---------------|----------------------------------|-----------|--------------------------|
| `cc-db`       | postgres:16-alpine               | 5432      | PostgreSQL database      |
| `cc-backend`  | maven build → eclipse-temurin:17 | —         | Spring Boot REST API (internal only; nginx proxies to it) |
| `cc-frontend` | node build → nginx:1.27-alpine   | 5173      | React SPA + `/api` proxy |

Then open **http://localhost:5173** and log in:

- Email: `alex@gisma.edu`
- Password: `password123`

The first build takes a few minutes (Maven downloads dependencies, Vite builds React). Subsequent runs are fast.

To stop: `Ctrl+C`, then `docker compose down`. To wipe the database too: `docker compose down -v`.

### Deploying to a VPS

The same `docker compose up --build -d` works on a VPS. The frontend nginx proxies `/api/*` to the backend over the internal Docker network, so the React bundle never needs to know the public address — it just works on `localhost`, on `http://YOUR_VPS_IP:5173`, or behind a domain.

Two practical notes:

1. **Open port 5173 in your firewall.** On Ubuntu: `sudo ufw allow 5173/tcp`. Or remap the published port to 80 in `docker-compose.yml` (`"80:80"` instead of `"5173:80"`) so users can visit `http://YOUR_DOMAIN` without a port.
2. **Backend port is intentionally not published.** It listens on the internal Docker network only. To call the API from outside, go through nginx: `curl http://YOUR_VPS_IP:5173/api/jobs/recommended`.

---

## Running without Docker

If you'd rather run things directly:

Prereqs: Java 17+, Maven 3.8+, Node.js 18+, PostgreSQL 13+ on port 5432.

1. Create the DB:

   ```bash
   psql -U postgres -c "CREATE DATABASE career_connect;"
   ```

   Update credentials in `backend/src/main/resources/application.properties` if your Postgres uses something other than `postgres` / `postgres`. Tables and seed data are created automatically on first start.

2. Backend:

   ```bash
   cd backend
   mvn spring-boot:run          # → http://localhost:8080
   ```

3. Frontend:

   ```bash
   cd frontend
   npm install
   npm run dev                  # → http://localhost:5173
   ```

---

## API reference

All endpoints except `/api/auth/**` and `/api/skills/all` require an `Authorization: Bearer <jwt>` header.

| Method | Path                          | Description                                |
|--------|-------------------------------|--------------------------------------------|
| POST   | `/api/auth/signup`            | Register a new student                     |
| POST   | `/api/auth/login`             | Log in, returns `{ token, email, name }`   |
| GET    | `/api/profile`                | Get current profile                        |
| PUT    | `/api/profile`                | Update name / university / course / year   |
| GET    | `/api/skills/all`             | Catalog of all skills (for suggestions)    |
| GET    | `/api/skills/me`              | My skills                                  |
| POST   | `/api/skills/me`              | Add a skill `{ "name": "Docker" }`         |
| DELETE | `/api/skills/me/{name}`       | Remove a skill                             |
| GET    | `/api/jobs/recommended`       | Ranked jobs (optional `?filter=internship`)|

---

## Project layout

```
docker-compose.yml          ← starts db + backend + frontend
backend/
  Dockerfile                ← maven build → JRE 17 runtime
  pom.xml
  src/main/java/com/gisma/career/
    CareerConnectApplication.java
    config/SecurityConfig.java
    controller/   (Auth, Profile, Skill, Job)
    dto/          (request/response objects)
    model/        (Student, Skill, Job)
    repository/   (Spring Data JPA)
    security/     (JwtUtil, JwtFilter)
    service/      (AuthService, SkillService, JobRecommendationService)
  src/main/resources/
    application.properties
    data.sql
frontend/
  Dockerfile                ← node build → nginx serve
  nginx.conf
  package.json
  vite.config.js
  index.html
  src/
    main.jsx, App.jsx, styles.css
    api/client.js
    components/   (Sidebar, JobCard)
    pages/        (Login, Dashboard, Profile)
```

---

## How match % is calculated

The recommender uses **content-based filtering**: each job and each student is
turned into a **TF-IDF weighted skill vector**, and jobs are ranked by **cosine
similarity** to the student.

1. **IDF (inverse document frequency)** — jobs are treated as "documents" and
   their required skills as "terms". A skill required by few jobs gets a high
   weight; a skill required by almost every job gets a low weight:

   ```
   idf(skill) = ln( (1 + N) / (1 + df) ) + 1
   ```

   where `N` = number of jobs and `df` = jobs requiring that skill. So matching
   a rare skill like *Kubernetes* counts for more than matching *SQL*.

2. **Cosine similarity** — the student vector and each job vector are compared:

   ```
   cosine = dot(student, job) / ( ||student|| * ||job|| )
   matchPercent = round(cosine * 100)
   ```

   Normalising by vector length means a job is not penalised just for listing
   many skills.

This is a non-parametric, instance-based method — there is no training step.
Scores are recomputed on every request, so adding or removing a skill instantly
updates the recommendations. Jobs are returned sorted by match % descending.
The logic lives in `JobRecommendationService`.

---

## Resetting demo data

With Docker:

```bash
docker compose down -v       # removes the postgres volume
docker compose up --build    # tables + seed data are recreated
```

Without Docker:

```bash
psql -U postgres -d career_connect -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

Then restart the backend — Hibernate will recreate the tables and `data.sql` will re-seed.
