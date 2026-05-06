# digital-syria-core-platform

Production-oriented MVP foundation for a unified citizen services pilot in Syria.

## Repository structure

- `frontend/` Next.js + TypeScript scaffold (Arabic RTL-ready)
- `backend/` FastAPI + SQLAlchemy + Alembic backend APIs
- `infra/` Infrastructure placeholders (Nginx reverse proxy)
- `docs/` Supplemental architecture and API notes
- `scripts/` Root-level helper scripts
- `PROJECT_STATUS.md` Current implementation status
- `AGENTS.md` Contributor/agent collaboration notes
- `SECURITY_NOTES.md` Security guardrails and secrets policy
- `MVP_SCOPE.md` Explicit MVP boundaries

## Quick start (local)

1. Copy envs:
   - `cp .env.example .env`
   - `cp backend/.env.example backend/.env`
2. Start stack:
   - `docker compose up --build`
3. Seed demo data:
   - `docker compose exec backend python backend/scripts/seed_data.py`
4. Open API docs:
   - Swagger UI: `http://localhost:8000/docs`
   - OpenAPI JSON: `http://localhost:8000/openapi.json`

## Backend local development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_data.py
pytest -q
uvicorn app.main:app --reload
```

## Demo users (seed data)

All demo accounts use password: `Passw0rd!`

- `citizen@demo.sy` (citizen)
- `employee@demo.sy` (employee)
- `supervisor@demo.sy` (supervisor)
- `admin@demo.sy` (admin)

## Notes

- UI text should remain Arabic formal with RTL layout for all user-facing pages.
- No real citizen data is used.
- Secrets must not be hardcoded for production environments.
