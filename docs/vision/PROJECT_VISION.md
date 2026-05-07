# Project Vision

## Why this project exists

This repository is the **first real MVP foundation** for a unified digital
government core for Syria. The goal is not to ship yet another isolated
ministry website, mobile app, or one-off project. The goal is to lay the
technical and organizational foundation for **shared national digital
infrastructure** that any government entity can build on.

The Syrian state today does not have a single, coherent, citizen-facing digital
platform. Citizens are routed through fragmented portals (when they exist at
all), redundant identity flows, inconsistent forms, and undocumented backend
integrations. Every ministry rebuilds the same primitives — authentication,
service catalogs, request workflows, audit, notifications — at lower quality,
in isolation, and without interoperability.

This project rejects that model.

## What we are building

A single, opinionated **government core platform** that provides:

- A **unified citizen portal** for submitting and tracking service requests.
- A **government workflow engine** so employees, supervisors, and administrators
  can review, route, comment on, and resolve those requests with full
  accountability.
- **Audit logs** for every state-changing action, so the system is transparent
  and reviewable.
- **Role-Based Access Control (RBAC)** distinguishing citizens, employees,
  supervisors, and administrators — with backend-enforced permissions, not just
  UI hiding.
- A clean, versioned **REST API** (`/api/v1`) designed for **interoperability**
  so other ministries, agencies, and future systems can integrate without
  reinventing primitives.
- A formal **Arabic, RTL** public interface that respects citizens as the
  primary users, not an afterthought.

## What this becomes over time

The MVP is intentionally narrow, but the architecture is chosen so that the
following can be added as real, production phases without rewriting the core:

- **National digital identity** — a real, government-issued digital ID
  integration replacing demo email/password authentication.
- **Government cloud hosting** — sovereign hosting with documented data
  residency, backups, key management, and operational runbooks.
- **National API gateway** — a centralized gateway that exposes ministry APIs
  through a single trust boundary, with quotas, observability, and policy
  enforcement.
- **Inter-ministry integrations** — verified data exchange between this core
  and ministry-specific systems (civil affairs, interior, finance, health,
  education, justice, etc.), replacing today's manual paper workflows.
- **Payment gateway integration** — official payment rails for fee collection.
- **Notification channels** — beyond in-app, expanding to SMS and email through
  vetted national providers.

These are **future phases**, not promises shipped today.

## What this is NOT (yet)

To prevent misunderstanding by future contributors, reviewers, and decision
makers, the following must be stated clearly and repeatedly:

- This MVP **uses mock data only**. Demo users, demo services, and demo
  requests exist solely so the platform can be exercised end-to-end.
- This is **not a production national system**. It is not certified, not
  hosted on government cloud, not connected to any real registry, and not
  integrated with any real identity provider.
- It does **not** process real citizen records.
- It does **not** process real payments.
- It does **not** make any compliance claim against any national or
  international standard.
- It must **not** be deployed publicly as if it were an official government
  service.

## How this MVP earns trust to grow

The MVP is the foundation that makes a real national platform fundable and
defensible. It does that by:

1. Showing a working, end-to-end vertical slice (citizen submits → employee
   processes → supervisor/admin observes → audit log records it).
2. Enforcing RBAC and auditability from day one, not as an afterthought.
3. Keeping all code, technical identifiers, file names, and comments in
   English so the codebase is reviewable by any engineer worldwide.
4. Keeping all citizen-facing text in **formal Arabic** with proper RTL
   layout, so the user experience is correct for Syrian citizens.
5. Documenting limitations honestly in `PROJECT_STATUS.md`,
   `SECURITY_NOTES.md`, and `MVP_SCOPE.md` so no one is misled into treating
   this MVP as more than it is.
