# VartaLang LMS Backend

Backend API for the VartaLang Learning Management System. The service is built
with Python, FastAPI, SQLAlchemy, PostgreSQL, and Alembic.

> **Private repository:** This project is owned and maintained by **Dhrupad
> Research Labs Pvt Ltd**. Its source code and documentation are not intended
> for public distribution.

## Features

- VartaLang SSO code exchange and JWT-based LMS sessions
- User profiles, login tracking, and daily learning streaks
- Course catalog, curriculum management, enrollments, and lesson progress
- Instructor profiles and course publishing workflows
- Practice labs and evaluation submissions
- Challenges and leaderboards
- Certification listing and certificate verification
- Articles and editorial content
- Career listings and job applications
- Admin operations and platform statistics
- Razorpay payment integration support

## Technology

- Python 3.10+
- FastAPI and Uvicorn
- SQLAlchemy 2.x and PostgreSQL
- Alembic database migrations
- Pydantic v2 and Pydantic Settings
- JWT authentication with `python-jose`
- `httpx` for VartaLang SSO verification
- Razorpay server-side SDK
- UUIDv7 identifiers through `uuid6`

## Project Structure

```text
vl-lms-backend/
├── app/
│   ├── api/v1/
│   │   ├── api.py                 # API v1 router aggregation
│   │   └── endpoints/             # Domain-specific route handlers
│   ├── core/
│   │   ├── config.py              # Environment-backed settings
│   │   ├── database.py            # SQLAlchemy engine and session dependency
│   │   └── security.py            # Password and JWT helpers
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic request and response schemas
│   ├── services/                  # Integrations such as SSO
│   └── main.py                    # FastAPI application
├── alembic/
│   └── versions/                  # Database migration revisions
├── .env.example                   # Local environment variable template
├── alembic.ini                    # Alembic configuration
├── main.py                        # Direct Uvicorn entry point
├── requirements.txt
└── README.md
```

## API

The API is mounted under `/api/v1`. The available route groups are:

| Prefix | Area |
| --- | --- |
| `/auth` | SSO exchange, development login, and current-user session |
| `/users` | User profiles and streaks |
| `/instructor` | Instructor profiles |
| `/courses` | Course catalog and curriculum management |
| `/enrollments` | Enrollment and lesson progress |
| `/practice` | Practice labs, progress, and evaluation |
| `/challenges` | Challenges and leaderboards |
| `/certifications` | Certification listing and verification |
| `/articles` | Articles and blog content |
| `/careers` | Job postings and applications |
| `/admin` | Administrative operations and analytics |

Interactive API documentation is generated from the application:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Local Development

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

Copy `.env.example` to `.env` and set values for your PostgreSQL database,
JWT secret, SSO shared secret, and Razorpay credentials:

```powershell
Copy-Item .env.example .env
```

`DATABASE_URL` accepts PostgreSQL URLs. The application normalizes
`postgres://` and plain `postgresql://` values to the SQLAlchemy
`postgresql+psycopg2://` form.

### 4. Apply database migrations

```bash
alembic upgrade head
```

Alembic reads the database URL from `.env` through `app.core.config.settings`.
Create a new migration after model changes with:

```bash
alembic revision --autogenerate -m "describe the change"
```

### 5. Start the development server

Using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

Or using the repository entry point:

```bash
python main.py
```

The root endpoint is `http://localhost:8000/`, and the health endpoint is
`http://localhost:8000/health`.

## Authentication

Protected endpoints use a bearer token:

```text
Authorization: Bearer <access-token>
```

The normal login flow exchanges a one-time VartaLang SSO code at
`POST /api/v1/auth/sso/exchange`. The development-only login endpoint is
`POST /api/v1/auth/dev-login`; it should not be enabled or exposed in
production.

## Configuration Reference

The supported settings are defined in `app/core/config.py` and include:

- `PROJECT_NAME`, `ENVIRONMENT`, `PORT`, and `DEBUG`
- `ENABLE_DEV_LOGIN` (disabled by default)
- `CORS_ORIGINS`
- `DATABASE_URL`
- `JWT_SECRET`, `JWT_ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES`
- `VARTALANG_MAIN_AUTH_URL` and `SSO_SHARED_SECRET`
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`

Never commit `.env` or production secrets. Use `.env.example` as the template
for local configuration.
