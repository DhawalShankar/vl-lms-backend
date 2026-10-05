# VartaLang LMS Backend (Python / FastAPI)

Scalable, modular Learning Management System and Community Chat backend for **VartaLang**, built with **Python 3.10+**, **FastAPI**, and **PostgreSQL**.

---

## 🏗 Architecture & Tech Stack

- **Framework:** FastAPI (High-performance async ASGI)
- **Database:** PostgreSQL (Hosted on Neon)
- **ORM:** SQLAlchemy 2.0 + Alembic (Migrations)
- **Validation & Settings:** Pydantic v2 + Pydantic-Settings
- **Security:** OAuth2 / JWT (python-jose), SSO exchange with Main VartaLang
- **Payments:** Razorpay Server-side SDK
- **Realtime Chat:** Native FastAPI WebSockets

---

## 📁 Project Directory Layout

```text
vl-lms-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py           # V1 Router Aggregator
│   │       └── endpoints/       # Domain-specific routes (auth, courses, chat, etc.)
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (.env management)
│   │   └── database.py          # SQLAlchemy Engine, SessionLocal, get_db dependency
│   ├── models/                  # SQLAlchemy ORM Models
│   ├── schemas/                 # Pydantic Request / Response DTOs
│   ├── services/                # Business logic (SSO, Razorpay, Chat WebSocket manager)
│   └── main.py                  # FastAPI Application Entrypoint
├── alembic/                     # Database migrations
├── .env.example                 # Environment variables template
├── requirements.txt             # Production & development dependencies
└── README.md
```

---

## 🚀 Local Development Setup

### 1. Create and Activate Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your local or Neon PostgreSQL credentials
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

- API Base: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Alternative ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`
