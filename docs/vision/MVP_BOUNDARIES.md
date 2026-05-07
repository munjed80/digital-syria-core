# MVP Boundaries

This document defines, in plain language, what **is** and **is not** in scope
for the current MVP of `digital-syria-core-platform`. It exists so that no
contributor, reviewer, government stakeholder, or end user is misled about the
maturity of this system.

If a feature is listed under "Out of scope", it is **not** implemented. Do not
claim it is. Do not ship it without first updating this document and the
corresponding documents in `docs/vision/`.

## In scope (MVP)

### Backend (FastAPI)

- JWT-based authentication with email + password (demo only).
- RBAC for four roles: `citizen`, `employee`, `supervisor`, `admin`.
- Service catalog APIs.
- Service request submission, listing, retrieval.
- Workflow status updates and internal notes (employee/supervisor/admin).
- In-app notifications model and basic notification endpoints
  (own-notifications-only).
- Audit log writes for state-changing actions; admin-only audit log read.
- Supervisor/admin dashboard summary endpoint.
- Structured JSON error responses.
- SQLAlchemy models + Alembic migrations.
- Demo seed script for users and services.

### Frontend (Next.js)

- Citizen Portal: landing, register/login, dashboard, services catalog,
  service application, "my requests" list, request detail, profile.
- MVP Employee portal page: list submitted requests, open detail, change
  status, add internal note.
- MVP Admin foundation page: high-level counts and a link to audit logs
  (placeholder).
- Arabic, formal, RTL layout throughout.
- Next.js middleware redirecting unauthenticated users on protected routes.

### Operations / docs

- Docker Compose definition and Nginx reverse-proxy placeholder.
- README, `PROJECT_STATUS.md`, `SECURITY_NOTES.md`, `MVP_SCOPE.md`, and the
  files in `docs/vision/`.

## Out of scope (future phases)

These are explicitly **not** part of the current MVP and **must not** be
claimed as working:

### Identity

- Real national digital identity integration.
- Government-issued eID / smart card login.
- Federation with external SSO providers.
- Biometric or device-bound authentication.

### Payments

- Real payment gateway integration.
- Fee collection, receipts, refunds, reconciliation.
- Any handling of bank or card data.

### Inter-ministry integrations

- Live data exchange with the Civil Affairs registry.
- Live data exchange with the Ministry of Interior, Justice, Finance, Health,
  Education, or any other ministry.
- Document verification against authoritative national registries.
- Cross-ministry case routing.

### Infrastructure

- Sovereign / government cloud hosting.
- National API gateway placement.
- High-availability or multi-region deployment.
- Production-grade key management (HSM/KMS).
- Centralized SIEM, secrets vault, or production observability stack.

### Notifications

- SMS delivery via a national provider.
- Email delivery via a national provider.
- Push notifications.
- Two-way notification flows.

### Compliance

- No formal compliance certification (ISO, SOC, GDPR, local equivalents) has
  been evaluated.
- No accessibility audit has been performed.
- No penetration test has been performed.
- No data protection impact assessment has been performed.

### Operational maturity

- No real incident response runbook.
- No real on-call rotation.
- No real backup/restore drill.
- No real disaster recovery plan.

## Hard rules for the MVP

1. **No real citizen data.** Ever. Including in tests, fixtures, screenshots,
   demos, or seed scripts.
2. **No fake production credentials.** Demo passwords are visibly demo
   (`Passw0rd!`).
3. **No misleading compliance claims.** If we have not certified it, we do not
   say we have.
4. **No external paid services.** No third-party SaaS dependencies that would
   block sovereign deployment.
5. **English code, Arabic UI.** File names, identifiers, comments, log
   messages, and error keys stay in English. Citizen-facing text stays in
   formal Arabic with RTL layout.
6. **Mock data is labeled as mock.** Anywhere demo data is exposed, the user
   must be able to tell it is a demo.

## When something graduates from "out of scope" to "in scope"

- Update `MVP_SCOPE.md` and this file.
- Update `PROJECT_STATUS.md` to reflect actual status.
- Add backend enforcement *before* exposing the feature in the UI.
- Add tests covering both the happy path and at least one authorization
  failure case.
- Update `SECURITY_NOTES.md` if the change affects the security posture.

This is how we keep the MVP honest while still letting it grow into the real
national platform it is meant to become.
