# Implementation Principles

These principles govern how this codebase is built. They are deliberately
strict because this project aspires to become **shared national digital
infrastructure**, not a throwaway demo. Every contributor — human or AI agent
— must follow them.

## 1. Backend is the source of truth

- All authorization decisions are made in the backend. Frontend role checks
  are a UX convenience only.
- Every state-changing endpoint requires authentication.
- Every state-changing endpoint enforces RBAC explicitly.
- The frontend never receives data the current user is not authorized to see.

## 2. RBAC is non-negotiable

- Four roles exist today: `citizen`, `employee`, `supervisor`, `admin`.
- Citizens may only see and act on **their own** data.
- Employees, supervisors, and admins act on government workflow data, scoped
  by role.
- Permission checks live next to the route handlers; they are not implicit.

## 3. Auditability is a feature, not a log line

- Every important action (request submission, status change, internal note,
  privileged read) writes an entry to the audit log.
- Audit entries record actor, action, entity, and a structured metadata blob.
- Audit logs are read-only and visible only to administrators.

## 4. API interoperability

- All public endpoints live under a versioned prefix: `/api/v1`.
- Schemas are explicit Pydantic models, not free-form dicts.
- Errors return structured JSON. Citizens see Arabic messages; the API contract
  stays stable in English keys.
- Breaking changes require a new version prefix.

## 5. Mock data only in the MVP

- Seed data is clearly demo data (demo users, demo services).
- No real names, real national IDs, real addresses, or real phone numbers are
  ever committed.
- No production credentials, API keys, or secrets are committed.
- No external paid services are wired in.

## 6. Honest documentation

- `PROJECT_STATUS.md` always reflects what is actually working, what was
  fixed, what remains, and current security limitations.
- `SECURITY_NOTES.md` describes real, current guardrails — not aspirations.
- `MVP_SCOPE.md` and `docs/vision/MVP_BOUNDARIES.md` define what is *out of
  scope* for this MVP, in plain language.
- We do not claim compliance with any national or international standard
  unless that compliance has been formally evaluated.

## 7. Language and locale discipline

- **Code, file names, identifiers, and comments are in English.** This keeps
  the codebase reviewable by any engineer.
- **User-facing UI text is in formal Arabic.** Layout is RTL.
- Error messages shown to citizens are in Arabic. Internal logs and audit
  entries are in English.

## 8. Security-first defaults

- Passwords are hashed with a vetted KDF (`bcrypt` via `passlib`).
- JWT secrets are configured per environment via env vars; defaults are for
  development only and clearly marked.
- CORS origins are an explicit allow-list.
- SQL access goes through SQLAlchemy / Alembic — no string-built queries.
- Input is validated at the schema layer before reaching business logic.

## 9. Small, complete, reviewable changes

- Each change is the smallest change that fully addresses its task.
- Each change ships with tests that exercise the new behavior.
- Existing tests must continue to pass.
- New dependencies are justified, pinned, and ecosystem-vetted.

## 10. Designed for replacement

- Today's email/password authentication will be replaced by a national digital
  identity provider. The auth dependency layer is the integration point.
- Today's in-app notifications will be extended to SMS/email via vetted
  national providers. The notifications model is the integration point.
- Today's local SQLite/Postgres deployment will move to government cloud. The
  database session layer and Alembic migrations are the integration points.
- Today's direct REST exposure will move behind a national API gateway. The
  `/api/v1` prefix and structured errors are the integration points.

If a feature cannot be built without violating one of these principles, the
correct answer is to **stop and discuss**, not to ship the violation.
