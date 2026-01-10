# TrustCheck

A production-ready, API-first, behavior-based payment trust scoring service for SMEs, landlords, cooperatives, and B2B vendors in emerging markets.

## What this system is

- Records payment behavior entered by businesses.
- Converts behavior into a simple, explainable trust score (0–100).
- Exposes risk bands and recommendations; raw score optionally.
- Multi-tenant with strict isolation.

## What this system is NOT

- Not a credit bureau.
- No external data integrations (banks, telcos, bureaus).
- No ML or opaque models.

## Tech stack

- FastAPI (ASGI)
- PostgreSQL
- SQLAlchemy (async)
- Pydantic v2
- Alembic migrations
- JWT auth
- RBAC
- Environment-based config
- Bcrypt password hashing
- Rate limiting
- Audit logging

## How to run

1. Create database:
   ```bash
   createdb trust
