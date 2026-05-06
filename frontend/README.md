# Frontend — Citizen Portal

Next.js (App Router, TypeScript) + Tailwind CSS implementation of the Arabic
RTL Citizen Portal that consumes the FastAPI backend.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev          # http://localhost:3000
```

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to point at the backend
(`http://localhost:8000/api/v1` by default).

## Scripts

- `npm run dev` — local dev server
- `npm run build` — production build (also acts as the type-check / validation step)
- `npm start` — run the production build
- `npm run lint` — Next.js linter

## Project layout

- `app/` — App Router pages
  - `app/login`, `app/register` — public auth pages
  - `app/dashboard`, `app/services`, `app/requests`, `app/profile` — protected
    portal pages, each wrapped in the shared `PortalShell`
- `components/` — `Navbar`, `PortalShell`, `ProtectedRoute`, `StatusBadge`
- `lib/api.ts` — typed fetch wrapper for the FastAPI endpoints
- `lib/auth-context.tsx` — JWT auth context with persistent session
- `lib/services-meta.ts` — service categorization and status localization
- `middleware.ts` — server-side redirect for protected routes when no token cookie

See the root `README.md` for the combined backend + frontend run instructions.
