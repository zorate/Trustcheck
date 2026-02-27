# TrustCheck Security Architecture

## Trust Model

TrustCheck operates on a **zero-trust between tenants** model.

Every business (tenant) is fully isolated. A business can only ever see, modify, or query data that belongs to it. This is not enforced by convention — it is enforced structurally at every database query.

---

## Threat Model

### Threats We Defend Against

| Threat | Mitigation |
|---|---|
| Cross-tenant data access | All queries scoped by `business_id` at service layer |
| IDOR (Insecure Direct Object Reference) | Compound queries: `{id, business_id}` — foreign IDs return 404 |
| Account enumeration | Constant-time login (bcrypt always runs, even for missing users) |
| Brute force | Rate limiting (60 req/min per IP) + bcrypt rounds = 12 |
| Token replay | JTI (unique token ID) in every JWT |
| Privilege escalation | Role rank enforced in dependency injection |
| Timing attacks on password | bcrypt.checkpw is constant-time |
| Phone number exposure | HMAC-SHA256 hash stored; raw number never persisted |
| Token type confusion | Access and refresh tokens have `type` claim validated separately |
| Information leakage | 404 (not 403) for cross-tenant access; no server headers |
| Input injection | Pydantic v2 validation on all inputs |
| Clickjacking | `X-Frame-Options: DENY` header |
| MIME sniffing | `X-Content-Type-Options: nosniff` |

### Threats Outside This System's Scope

- Network-level attacks (handled by load balancer / API gateway)
- DDoS (handled by CDN / WAF layer)
- Physical server security
- MongoDB network security (use VPC, auth, TLS)

---

## Authentication Flow

```
Client                   TrustCheck API              MongoDB
  │                           │                          │
  │  POST /auth/login          │                          │
  │ {email, password}  ──────►│                          │
  │                           │  find user by email ────►│
  │                           │◄──────────────── user ───│
  │                           │                          │
  │                           │  bcrypt.checkpw()        │
  │                           │  (always runs — even     │
  │                           │   if user not found)     │
  │                           │                          │
  │◄─── 401 (if invalid) ─────│                          │
  │                           │                          │
  │◄─── access_token ─────────│                          │
  │     refresh_token         │                          │
```

---

## Tenant Isolation Implementation

Every service function receives `business_id` from the authenticated token:

```python
# ✅ CORRECT — tenant-scoped query
person = await Person.find_one(
    Person.id == person_id,
    Person.business_id == business_id,  # ← enforces isolation
)

# ❌ WRONG — would be an IDOR vulnerability
person = await Person.get(person_id)
```

The `business_id` in the token cannot be forged without the `SECRET_KEY`. The token is validated on every request in `get_current_user()`.

---

## Phone Number Privacy

```
Input phone:   "080-1234-5678"
       ↓
Normalise:     "08012345678"
       ↓
HMAC-SHA256:   hmac(salt, "08012345678") → "a3f8c2..."
       ↓
Stored:        phone_hash = "a3f8c2..."
               phone_display = "****5678"
```

The HMAC salt is a server-side secret (`PHONE_HASH_SALT`). Without this secret, the hash cannot be reversed or brute-forced against a rainbow table.

---

## Role-Based Access Control

```
owner  ──► can do everything + manage staff
  │
  ▼
admin  ──► manage persons, payments, view full score breakdown
  │
  ▼
staff  ──► record payments, add persons, view score summary
```

Roles are embedded in the JWT and validated via `require_role()` dependency:

```python
@router.post("/staff", dependencies=[Depends(require_role("owner"))])
```

A staff member cannot escalate to admin or owner by modifying the request — the token claim is validated server-side.

---

## Security Headers

Every response includes:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Cache-Control` | `no-store` | Prevent response caching |
| `Strict-Transport-Security` | `max-age=31536000` | Force HTTPS |

The `Server` header is removed to avoid fingerprinting.

---

## Audit Log

All sensitive operations write to the `audit_logs` collection:

- Records are **append-only** — never updated, never soft-deleted
- Scoped to `business_id` — a business can only query its own logs
- Contains no PII — no raw phone numbers, passwords, or financial data
- Accessible only by the `owner` role

Audit log entries cannot be deleted via the API.

---

## Production Checklist

Before deploying to production:

- [ ] Generate a strong `SECRET_KEY` (64+ random chars): `openssl rand -hex 64`
- [ ] Generate a strong `PHONE_HASH_SALT` (32+ random chars): `openssl rand -hex 32`
- [ ] Set `ENVIRONMENT=production` (disables /docs, /redoc, /openapi.json)
- [ ] Configure MongoDB with authentication and TLS
- [ ] Place MongoDB in a private VPC — never expose port 27017 publicly
- [ ] Use MongoDB Atlas or configure replica set for HA
- [ ] Set up TLS termination at the load balancer
- [ ] Replace in-process rate limiter with Redis-backed solution for multi-worker deployments
- [ ] Configure ALLOWED_ORIGINS to your production frontend URL only
- [ ] Set up log aggregation (the app writes structured logs to stdout)
- [ ] Set `BCRYPT_ROUNDS=12` minimum in production