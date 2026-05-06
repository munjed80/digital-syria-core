# digital-syria-core-platform

Production-oriented MVP foundation for a unified citizen services pilot in Syria.

## Repository structure

- `frontend/` Next.js + TypeScript Citizen Portal (Arabic RTL, Tailwind CSS)
- `backend/` FastAPI + SQLAlchemy + Alembic backend APIs
- `infra/` Infrastructure placeholders (Nginx reverse proxy)
- `docs/` Supplemental architecture and API notes
- `scripts/` Root-level helper scripts
- `PROJECT_STATUS.md` Current implementation status
- `AGENTS.md` Contributor/agent collaboration notes
- `SECURITY_NOTES.md` Security guardrails and secrets policy
- `MVP_SCOPE.md` Explicit MVP boundaries

## Quick start (local, full stack)

The project is split into two services that run together: the FastAPI backend
(default port `8000`) and the Next.js citizen portal (default port `3000`).

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
PYTHONPATH=. python scripts/seed_data.py   # demo users + service catalog
uvicorn app.main:app --reload              # http://localhost:8000
```

The API is mounted at `http://localhost:8000/api/v1` and exposes Swagger UI at
`http://localhost:8000/docs`.

CORS for the local frontend (`http://localhost:3000`) is enabled by default and
can be overridden via the `CORS_ALLOW_ORIGINS` env var (comma-separated list).

### 2. Frontend (Citizen Portal)

In a separate terminal:

```bash
cd frontend
cp .env.example .env.local            # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
npm install
npm run dev                           # http://localhost:3000
```

Production build:

```bash
cd frontend
npm run build
npm start
```

### 3. Docker (optional)

```bash
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up --build
docker compose exec backend python backend/scripts/seed_data.py
```

## Citizen Portal — pages

| Route | Purpose |
| --- | --- |
| `/` | Public landing page |
| `/login` | JWT login (FastAPI `POST /auth/token`) |
| `/register` | Citizen registration (`POST /auth/register`) |
| `/dashboard` | Authenticated home — overview & recent requests |
| `/services` | Government service catalog grouped by category |
| `/services/[id]/apply` | Submit a new request for the chosen service |
| `/requests` | "My Requests" table with status filter |
| `/requests/[id]` | Request detail with status-history timeline |
| `/profile` | Account info + logout |

Authentication uses a JWT bearer token persisted to `localStorage` and
mirrored to a `dsc_access_token` cookie so that the Next.js middleware can
redirect unauthenticated users away from protected routes.

## Verification flow

1. Start the backend and seed demo data.
2. Start the frontend.
3. Open `http://localhost:3000`, click **إنشاء حساب**, register a citizen.
4. You will be auto-logged-in and redirected to `/dashboard`.
5. Open **كتالوج الخدمات**, click **تقديم طلب** on any service, submit.
6. A success screen shows the tracking ID; the request appears in **طلباتي**.

## Demo users (seed data)

All demo accounts use password: `Passw0rd!`

- `citizen@demo.sy` (citizen)
- `employee@demo.sy` (employee)
- `supervisor@demo.sy` (supervisor)
- `admin@demo.sy` (admin)

## Tests

```bash
cd backend && pytest -q
cd frontend && npm run build
```

## Notes

- UI text remains Arabic formal with RTL layout for all user-facing pages.
- No real citizen data is used.
- Secrets must not be hardcoded for production environments.
- The frontend stores the JWT in `localStorage` + a cookie for MVP convenience.
  A production hardening step is to migrate to HttpOnly cookies issued by the
  backend.
