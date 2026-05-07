# PROJECT STATUS

## Completed in this iteration

### Vision and documentation

- Added `docs/vision/PROJECT_VISION.md` describing the project as the first
  real MVP foundation for unified national digital infrastructure.
- Added `docs/vision/IMPLEMENTATION_PRINCIPLES.md` documenting the rules
  every change must follow (backend-as-source-of-truth, RBAC, audit,
  interoperability, language discipline, security defaults).
- Added `docs/vision/MVP_BOUNDARIES.md` listing what is in scope today and
  what is explicitly a future phase (national identity, payments, ministry
  integrations, government cloud, API gateway).
- Updated `README.md` with a Project Vision section linking to the three
  vision documents and a clear MVP status (backend ✅, citizen portal ✅,
  employee/supervisor/admin portals in progress, real identity / payments /
  ministry integrations explicitly future phases).

### Backend

- Added basic notifications API:
  - `GET /api/v1/notifications` returns only the current user's notifications
    (citizens see their own; employees/supervisors/admins see their own).
  - `PATCH /api/v1/notifications/{id}/read` marks one of the current user's
    notifications as read; attempting to mark another user's notification
    returns `404` (to avoid leaking existence).
- Added Pydantic schema `NotificationPublic` and registered the new router
  in `app/main.py`.
- Added `backend/tests/test_notifications.py` covering: listing returns
  only own notifications (citizen and employee), unauthenticated access is
  rejected, marking own notification works and is idempotent, marking
  another user's notification returns 404, marking unknown id returns 404.

### Frontend

- Added a protected MVP employee portal page at `/employee/requests` that
  lists submitted requests, opens a detail view, allows changing the
  request status, and allows adding an internal note. Errors (including
  403 / 404 / network) are shown clearly in Arabic.
- Added a protected MVP `/admin` foundation page showing services count,
  requests count, a users placeholder, a link/reference to the audit logs
  endpoint placeholder, and an explicit notice that this is the MVP admin
  foundation — not the full admin console.
- Extended `ProtectedRoute` and `PortalShell` to accept an `allowedRoles`
  whitelist (UX gating only — backend RBAC remains the source of truth).
- Extended Next.js `middleware.ts` so that `/employee/*` and `/admin/*` are
  treated as protected routes that require an auth cookie.
- Added API client methods `updateRequestStatus`, `addInternalNote`, and
  `dashboardSummary` to `frontend/lib/api.ts`.

## What was fixed

- **Frontend build (Task 3).** Investigated `cd frontend && npm ci && npm
  run build`. The build **completed successfully** end-to-end (compile,
  type-check, page-data collection, static page generation, optimization,
  and trace collection) with no hangs and no errors. No fix was required.
  Diagnosis confirmed:
  - **Dynamic routes** (`/requests/[id]`, `/services/[id]/apply`) are
    correctly marked as `ƒ` (server-rendered on demand) because they call
    `useParams()` inside client components — Next.js handles them correctly.
  - **Client components** (`'use client'`) under `/dashboard`,
    `/services`, `/requests`, `/profile` use `useEffect` for data fetching,
    so they don't block static generation.
  - **`middleware.ts`** matches only protected routes and `/login` /
    `/register`; it does not import server-only APIs at module top-level.
  - No page calls server-only data fetching APIs that would block static
    generation.
  - The new `/employee/requests` and `/admin` pages also build cleanly as
    static pages (their data is fetched client-side after auth loads).

## Commands run

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q

# Frontend
cd frontend
npm ci
npm run build
npx tsc --noEmit
```

## Test / build results

- **Backend tests:** `pytest -q` → **9 passed** (3 pre-existing + 6 new
  notification tests).
- **Frontend build:** `npm run build` → **success**, all 12 routes built
  (10 static, 2 dynamic), no warnings beyond the standard Next.js
  telemetry/cache notices.
- **TypeScript check:** `npx tsc --noEmit` → **success, no errors**.

## What still remains

- Full supervisor portal UI (currently the supervisor reads from the same
  dashboard summary endpoint as the admin).
- Full admin console: user management, role management, services
  administration, full audit-log viewer UI, system settings.
- Notifications: extend beyond persisted in-app records to SMS/email
  channels via vetted national providers.
- Reporting / analytics dashboard with visualizations.
- CI workflow automation (lint, type-check, security scans).
- Keycloak / national SSO integration adapter layer.
- Migration plan from `localStorage` + non-HttpOnly cookie to HttpOnly
  cookies issued by the backend.

## Known security limitations

- **JWT in `localStorage` + non-HttpOnly cookie.** This is a pragmatic
  trade-off for the MVP so the Next.js middleware can perform server-side
  redirects on protected routes. It is **not** suitable for production: the
  cookie is readable by JavaScript and is therefore vulnerable to XSS
  exfiltration. Production hardening: switch to HttpOnly, Secure,
  SameSite=Strict cookies issued by the backend.
- **Frontend role gating is UX-only.** `ProtectedRoute` and `PortalShell`
  hide pages based on the user role, but the backend remains the source of
  truth. Every state-changing or sensitive endpoint enforces RBAC server-side
  via `require_roles(...)`.
- **Demo credentials.** Seed users (`citizen@demo.sy`, `employee@demo.sy`,
  `supervisor@demo.sy`, `admin@demo.sy`, password `Passw0rd!`) are visibly
  demo. They must never be used in any environment that is reachable from
  the public internet or contains real data.
- **JWT secret.** `JWT_SECRET_KEY` defaults to a development value and must
  be overridden via env var in any non-development deployment.
- **No real national identity, no real payment gateway, no real ministry
  integrations.** This MVP uses mock data only. It is **not** a production
  national system. See `docs/vision/MVP_BOUNDARIES.md`.
- **No formal compliance.** No ISO/SOC/national-equivalent certification,
  no accessibility audit, and no penetration test has been performed
  against this codebase.
