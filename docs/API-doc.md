
> Artifact: `docs/ARCHITECTURE.md`
```markdown
# Architecture

## Overview

- **API-first** FastAPI service.
- **Multi-tenant** isolation via `business_id` in JWT and query scoping.
- **PostgreSQL** for persistence.
- **Async SQLAlchemy** for DB access.
- **Alembic** for migrations.
- **Audit middleware** logs all API calls.

## Components

- `core/`: configuration, database, security, rate limiting.
- `middleware/`: auth, audit, tenant scope enforcement.
- `models/`: ORM entities with UUIDs, timestamps, soft deletes.
- `schemas/`: Pydantic v2 request/response models.
- `services/`: scoring engine, hashing, RBAC, audit helpers.
- `api/v1/`: versioned endpoints.
- `migrations/`: Alembic migration scripts.

## Data flow

1. Business registers → Business + Admin user created.
2. Staff logs payments and references for persons (subjects).
3. Scoring engine computes trust score from system-observed behavior.
4. Scores stored and retrievable per business-person pair.
5. Audit logs record API calls for traceability.

## Trust boundaries

- **External clients**: Untrusted; all inputs validated.
- **Auth tokens**: Trusted only after verification; scopes enforced.
- **Database**: Trusted store; queries scoped by tenant.
- **Scoring**: Uses only system data; no external sources.

## Tenant isolation

- JWT includes `bid` (business_id).
- All queries filter by `business_id`.
- Cross-tenant access denied by middleware checks.
- No shared endpoints returning mixed data.

## Cold start handling

- New person with no history:
  - Payment History: 15 points.
  - Consistency: 5 points.
  - Relationship Duration: 5 points.
  - Capacity: 5 points.
  - Reference: 0 points.
  - Total: 30 → High Risk → Do not extend credit.
- As behavior accumulates, scores update via `/scoring/compute`.

## Audit logging

- Middleware logs path, method, IP, user, business, status code.
- Admins can view audit logs via `/api/v1/system/audit`.
