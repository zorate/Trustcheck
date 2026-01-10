# Security

## Principles

- **Least privilege**: Scopes restrict actions.
- **Defense in depth**: JWT, RBAC, rate limiting, audit logging.
- **Zero trust between tenants**: No cross-tenant data access.
- **Secure defaults**: Strong hashing, validated inputs, safe outputs.

## Authentication

- JWT access and refresh tokens.
- Access tokens short-lived; refresh tokens longer-lived.
- Tokens include `sub` (user_id), `bid` (business_id), `scp` (scopes), `typ` (type).

## Authorization

- `admin` scope required for staff management and audit logs.
- `staff` scope for operational endpoints.

## Data protection

- Phone numbers hashed with HMAC-SHA256 + salt.
- No raw phone storage.
- Soft deletes to preserve auditability.

## Threat mitigations

- **IDOR**: Resource access validated against `business_id`.
- **Enumeration**: Rate limiting per IP+path; UUIDs not predictable.
- **Replay**: Token expirations; refresh flow; audit trails.
- **Privilege escalation**: Scope checks; admin-only endpoints.
- **Timing attacks**: Passlib hashing; JWT verification.

## Input validation

- Pydantic v2 schemas enforce types, lengths, patterns.
- Server-side checks for tenant scope and resource ownership.

## Output filtering

- Responses include only tenant-owned data.
- No leakage of other tenants’ data.

## Secure operations

- Alembic migrations for controlled schema changes.
- No external data integrations.
