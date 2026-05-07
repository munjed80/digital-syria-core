# digital-syria-core-platform

Production-oriented MVP foundation for a unified citizen services pilot in Syria.

## Project Vision

This repository is the **first real MVP foundation** for a unified digital
government core for Syria. The goal is not scattered ministry applications,
but **shared national digital infrastructure** built around a unified citizen
portal, an auditable government workflow engine, RBAC, and an interoperable
versioned API.

Read the vision documents before contributing:

- [`docs/vision/PROJECT_VISION.md`](docs/vision/PROJECT_VISION.md) — what this
  project is, what it becomes, and what it is not.
- [`docs/vision/IMPLEMENTATION_PRINCIPLES.md`](docs/vision/IMPLEMENTATION_PRINCIPLES.md)
  — the rules every change must follow (backend-as-source-of-truth, RBAC,
  audit, interoperability, language discipline, security defaults).
- [`docs/vision/MVP_BOUNDARIES.md`](docs/vision/MVP_BOUNDARIES.md) — what is
  in scope today and what is explicitly a future phase.

### Current MVP status

- **Backend foundation:** implemented (FastAPI + SQLAlchemy + Alembic, JWT
  auth, RBAC, services catalog, requests workflow, audit logs, in-app
  notifications, dashboard summary).
- **Citizen portal:** implemented (Next.js, formal Arabic, RTL).
- **Employee portal:** in progress — an MVP `/employee/requests` page exists
  for listing, opening, status changes, and internal notes.
- **Supervisor portal:** in progress — uses the dashboard summary endpoint;
  a dedicated UI is not yet built.
- **Admin portal:** in progress — an MVP `/admin` foundation page exists
  with high-level counts and a link to audit logs (placeholder).
- **Real national identity, payment gateway, and ministry integrations** are
  **future phases** and are explicitly out of scope for this MVP.
- **Mock data only.** This is **not** a production national system.

## Repository structure

- `frontend/` Next.js + TypeScript Citizen Portal (Arabic RTL, Tailwind CSS)
- `backend/` FastAPI + SQLAlchemy + Alembic backend APIs
- `infra/` Infrastructure placeholders (Nginx reverse proxy)
- `docs/` Supplemental architecture and API notes (see `docs/vision/` for the
  project vision, implementation principles, and MVP boundaries)
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
| `/employee/requests` | Employee/supervisor/admin: list requests, open, change status, add internal note |
| `/admin` | MVP admin foundation: counts and audit-logs link |

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
