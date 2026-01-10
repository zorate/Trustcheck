# Quick Start Guide

Get the Trust Scoring Service running in 5 minutes.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Git

## Option 1: Automated Setup (Recommended)

```bash
# Clone repository
git clone <repo-url>
cd trust-scoring-service

# Run setup script
chmod +x setup.sh
./setup.sh

# Start the application
source venv/bin/activate
make run
```

Visit: http://localhost:8000/api/docs

## Option 2: Manual Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY and PHONE_HASH_SALT
```

Generate secrets:
```python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start Database

**With Docker:**
```bash
docker-compose up -d postgres
```

**Without Docker:**
```bash
# Create database
createdb trust_scoring

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/trust_scoring
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Application

```bash
uvicorn app.main:app --reload
```

## Option 3: Docker (Full Stack)

```bash
# Start everything
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head

# View logs
docker-compose logs -f
```

Visit: http://localhost:8000/api/docs

## First Steps

### 1. Register a Business

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "My Business",
    "business_type": "SME",
    "business_email": "business@example.com",
    "business_phone": "+2348012345678",
    "user_full_name": "John Doe",
    "user_email": "john@example.com",
    "user_password": "SecurePass123!"
  }'
```

Save the `access_token` from the response.

### 2. Add a Person

```bash
curl -X POST http://localhost:8000/api/v1/persons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+2348098765432",
    "full_name": "Jane Smith",
    "relationship_type": "customer",
    "occupation": "Trader"
  }'
```

Save the `person.id` from the response.

### 3. Record a Payment

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "person_id": "PERSON_ID",
    "amount": 50000,
    "currency": "NGN",
    "description": "Payment for goods",
    "due_date": "2026-02-01T00:00:00Z"
  }'
```

### 4. Compute Trust Score

```bash
curl -X POST http://localhost:8000/api/v1/scoring/PERSON_ID/compute \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Verify Installation

### Health Check
```bash
curl http://localhost:8000/api/v1/system/health
```

Expected: `{"status":"healthy","timestamp":"..."}`

### API Documentation
Visit: http://localhost:8000/api/docs

### Run Tests
```bash
pytest tests/ -v
```

## Common Issues

### Database Connection Error
```
Error: could not connect to database
```

**Solution:**
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- If using Docker: `docker-compose ps`

### Port Already in Use
```
Error: Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### Migration Errors
```
Error: Can't locate revision identified by 'xxx'
```

**Solution:**
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Import Errors
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
- Ensure you're in project root directory
- Virtual environment is activated
- Dependencies are installed: `pip install -r requirements.txt`

## Next Steps

1. **Read Documentation**
   - [README.md](README.md) - Overview
   - [API.md](docs/API.md) - API Reference
   - [SCORING_LOGIC.md](docs/SCORING_LOGIC.md) - How scoring works

2. **Import Postman Collection**
   - File: `Trust-Scoring-API.postman_collection.json`
   - Set variables: `base_url`, `access_token`

3. **Explore the API**
   - Interactive docs: http://localhost:8000/api/docs
   - Try different endpoints
   - Test scoring with different scenarios

4. **Production Deployment**
   - See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
   - Update environment variables
   - Enable HTTPS
   - Set up monitoring

## Useful Commands

```bash
# Development
make run          # Start dev server
make test         # Run tests
make format       # Format code
make lint         # Check code quality

# Database
make migrate      # Create migration
make upgrade      # Apply migrations
make downgrade    # Rollback migration

# Docker
make docker-up    # Start services
make docker-down  # Stop services
make docker-logs  # View logs
```

## Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design
- Open an issue for bugs or questions

---

**You're ready to go!** 🚀

Start building trust scores for your business.