# Production Deployment Checklist

## Pre-Deployment Security

### 1. Environment Variables
- [ ] Generate strong SECRET_KEY (32+ random characters)
- [ ] Generate unique PHONE_HASH_SALT
- [ ] Set DEBUG=False
- [ ] Configure production DATABASE_URL
- [ ] Set appropriate CORS_ORIGINS
- [ ] Review and adjust RATE_LIMIT settings
- [ ] Set ENVIRONMENT=production

### 2. Database
- [ ] Production PostgreSQL instance provisioned
- [ ] Database user with appropriate permissions created
- [ ] Connection pooling configured (DATABASE_POOL_SIZE)
- [ ] Backups scheduled (daily minimum)
- [ ] Point-in-time recovery enabled
- [ ] SSL/TLS connection enforced

### 3. Application Security
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] Security headers configured (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting tested
- [ ] Input validation verified
- [ ] SQL injection protection confirmed (using ORM)
- [ ] XSS protection verified (Pydantic validation)

## Deployment Steps

### 1. Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd trust-scoring-service

# Set up environment
cp .env.example .env
# Edit .env with production values

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 2. Docker Deployment (Recommended)

```bash
# Build image
docker build -t trust-scoring-service:1.0 .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl https://your-domain.com/api/v1/system/health
```

### 3. Manual Deployment

```bash
# Install systemd service
sudo cp trust-scoring.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trust-scoring
sudo systemctl start trust-scoring

# Check status
sudo systemctl status trust-scoring
```

## Post-Deployment Verification

### 1. Smoke Tests

- [ ] Health endpoint returns 200
- [ ] Registration endpoint works
- [ ] Login endpoint works
- [ ] Token refresh works
- [ ] Rate limiting triggers correctly
- [ ] CORS headers present
- [ ] HTTPS enforced

### 2. Security Verification

- [ ] No DEBUG messages in production logs
- [ ] Password hashing working (Argon2)
- [ ] Phone hashing working
- [ ] JWT tokens have correct expiration
- [ ] Audit logs being created
- [ ] Tenant isolation verified (test with 2 businesses)

### 3. Performance Checks

- [ ] Database connection pool healthy
- [ ] Response times acceptable (<500ms for simple queries)
- [ ] Score computation completes within 2 seconds
- [ ] No memory leaks after 1000 requests

## Monitoring Setup

### 1. Application Monitoring

```python
# Add to monitoring dashboard:
- Request rate (requests/minute)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Active users count
```

### 2. Database Monitoring

- [ ] Query performance tracking
- [ ] Slow query log enabled
- [ ] Connection count monitored
- [ ] Disk usage alerts set

### 3. Security Monitoring

- [ ] Failed login attempts tracked
- [ ] Rate limit hits logged
- [ ] Unusual access patterns detected
- [ ] Audit log review scheduled (weekly)

## Backup Strategy

### 1. Database Backups

- [ ] Automated daily backups
- [ ] Backup retention: 30 days
- [ ] Test restore procedure quarterly
- [ ] Off-site backup storage

### 2. Application Backups

- [ ] Environment variables backed up (securely)
- [ ] Configuration files versioned
- [ ] Docker images tagged and stored

## Maintenance Tasks

### Daily
- [ ] Monitor error logs
- [ ] Check system health endpoint
- [ ] Review failed login attempts

### Weekly
- [ ] Review audit logs for anomalies
- [ ] Check database performance
- [ ] Verify backup success

### Monthly
- [ ] Security patch review and application
- [ ] Database optimization (VACUUM, ANALYZE)
- [ ] Audit log cleanup (retain 365 days)
- [ ] Review and rotate secrets if needed

### Quarterly
- [ ] Disaster recovery test
- [ ] Security audit
- [ ] Dependency updates
- [ ] Performance review

## Scaling Considerations

### When to Scale

Scale when:
- Response time p95 > 1 second
- Database CPU > 80%
- Memory usage > 85%
- Request rate approaching rate limits

### Horizontal Scaling

1. **Application Layer**
   - Stateless design allows easy scaling
   - Add instances behind load balancer
   - No session state stored

2. **Database Layer**
   - Start with read replicas
   - Use connection pooling
   - Consider sharding by business_id if needed

## Incident Response

### Critical Issues

**Database Down**
- [ ] Check database status
- [ ] Verify connection credentials
- [ ] Check network connectivity
- [ ] Failover to replica if available

**High Error Rate**
- [ ] Check application logs
- [ ] Verify database connections
- [ ] Check external dependencies
- [ ] Roll back recent deployments if needed

**Security Breach Suspected**
- [ ] Rotate all secrets immediately
- [ ] Review audit logs
- [ ] Check for unauthorized access
- [ ] Notify affected users
- [ ] Document incident

## Contact Information

**On-Call Rotation**
- Primary: [contact]
- Secondary: [contact]
- Escalation: [contact]

**External Services**
- Database Provider: [support link]
- Hosting Provider: [support link]
- Security Team: [contact]

## Compliance

- [ ] Data retention policy documented
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] GDPR compliance verified (if applicable)
- [ ] Data processing agreement signed

## Success Criteria

Deployment is successful when:
- ✅ All health checks passing
- ✅ Zero critical errors in first 24 hours
- ✅ First business successfully registered
- ✅ First trust score computed
- ✅ Audit logs being created
- ✅ Backups running successfully
- ✅ Monitoring alerts configured
- ✅ Response times within SLA

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Approved By**: _______________

**Sign-Off**: _______________