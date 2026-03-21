# Sliples Deployment Guide

Comprehensive deployment guide for the Sliples Web UI Automation Testing Platform.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Compose Configuration](#docker-compose-configuration)
3. [OpenShift Deployment](#openshift-deployment)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Scaling Considerations](#scaling-considerations)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)

---

## Local Development Setup

### Prerequisites

- **Docker:** Version 20.10 or later
- **Docker Compose:** Version 2.0 or later (included with Docker Desktop)
- **Git:** For cloning repositories
- **8GB RAM minimum:** For running all containers

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/sliples.git
cd sliples

# Copy environment template
cp .env.example .env

# Configure Google OAuth (optional for SSO)
# Edit .env and set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Check logs
docker compose logs -f
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Web UI |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | Object storage admin |
| PostgreSQL | localhost:5433 | Database (mapped to avoid conflicts) |
| Redis | localhost:6380 | Queue/cache |

### Development Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Rebuild containers after code changes
docker compose build

# View logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend

# Access database
docker compose exec postgres psql -U sliples -d sliples

# Access Redis CLI
docker compose exec redis redis-cli

# Run database migrations
docker compose exec backend alembic upgrade head

# Create initial admin API key
docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import ApiKey
import secrets
import bcrypt

db = SessionLocal()
key = secrets.token_hex(32)
key_hash = bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()
api_key = ApiKey(name='admin', key_hash=key_hash, key_prefix=key[:8])
db.add(api_key)
db.commit()
print(f'API Key: {key}')
"
```

### Running Tests

```bash
# Backend tests
docker compose exec backend pytest

# Frontend tests
docker compose exec frontend npm test

# Integration tests
docker compose exec backend pytest tests/integration/
```

---

## Docker Compose Configuration

### Architecture Overview

```
                    ┌─────────────────┐
                    │    Frontend     │
                    │   (React/Vite)  │
                    │   Port: 5173    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Backend     │
                    │    (FastAPI)    │
                    │   Port: 8000    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   PostgreSQL  │   │     Redis     │   │     MinIO     │
│  Port: 5433   │   │  Port: 6380   │   │  Port: 9000   │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
                    ┌───────▼───────┐
                    │ Celery Worker │
                    │ + Beat        │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼───────┐ ┌────▼────┐ ┌───────▼───────┐
    │ Browser Chrome│ │ Firefox │ │ (extensible)  │
    │  Port: 3001   │ │  3002   │ │               │
    └───────────────┘ └─────────┘ └───────────────┘
```

### docker-compose.yml Configuration

The default `docker-compose.yml` includes all necessary services:

```yaml
services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: sliples
      POSTGRES_PASSWORD: sliples_dev
      POSTGRES_DB: sliples
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sliples"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis for Celery
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: sliples
      MINIO_ROOT_PASSWORD: sliples_dev
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://sliples:sliples_dev@postgres:5432/sliples
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      # ... additional env vars
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Celery Worker
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
    environment:
      DATABASE_URL: postgresql://sliples:sliples_dev@postgres:5432/sliples
      REDIS_URL: redis://redis:6379/0
      BROWSER_CHROME_URL: ws://browser-chrome:3000
    depends_on:
      - postgres
      - redis
      - browser-chrome

  # Celery Beat (Scheduler)
  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.workers.celery_app beat --loglevel=info
    depends_on:
      - postgres
      - redis

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules

  # Playwright Browser (Chrome)
  browser-chrome:
    image: mcr.microsoft.com/playwright:v1.58.0-jammy
    command: npx playwright run-server --port 3000
    ports:
      - "3001:3000"
    shm_size: 2gb

  # Playwright Browser (Firefox)
  browser-firefox:
    image: mcr.microsoft.com/playwright:v1.58.0-jammy
    environment:
      BROWSER: firefox
    command: npx playwright run-server --port 3000
    ports:
      - "3002:3000"
    shm_size: 2gb

volumes:
  postgres_data:
  minio_data:
```

### Override for Production

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    volumes: []  # No mounted volumes in production
    environment:
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: ${DATABASE_URL}

  frontend:
    build:
      target: production
    volumes: []

  worker:
    command: celery -A app.workers.celery_app worker --loglevel=warning --concurrency=8
    volumes: []
```

Run with: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

---

## OpenShift Deployment

### Prerequisites

- OpenShift 4.x cluster
- `oc` CLI tool configured
- Persistent storage provisioner
- S3-compatible object storage (external or MinIO)

### Namespace Setup

```bash
# Create namespace
oc new-project sliples

# Create secrets
oc create secret generic sliples-db-credentials \
  --from-literal=username=sliples \
  --from-literal=password=<secure-password>

oc create secret generic sliples-s3-credentials \
  --from-literal=access-key=<access-key> \
  --from-literal=secret-key=<secret-key>

oc create secret generic sliples-google-oauth \
  --from-literal=client-id=<google-client-id> \
  --from-literal=client-secret=<google-client-secret>

oc create secret generic sliples-jwt-secret \
  --from-literal=secret=<jwt-secret-key>
```

### Deployment Manifests

#### PostgreSQL Deployment

```yaml
# openshift/postgres/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sliples-postgres
  namespace: sliples
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sliples-postgres
  template:
    metadata:
      labels:
        app: sliples-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: sliples-db-credentials
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: sliples-db-credentials
                  key: password
            - name: POSTGRES_DB
              value: sliples
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
      volumes:
        - name: postgres-data
          persistentVolumeClaim:
            claimName: sliples-postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: sliples-postgres-svc
  namespace: sliples
spec:
  selector:
    app: sliples-postgres
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sliples-postgres-pvc
  namespace: sliples
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### Backend Deployment

```yaml
# openshift/backend/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sliples-backend
  namespace: sliples
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sliples-backend
  template:
    metadata:
      labels:
        app: sliples-backend
    spec:
      containers:
        - name: backend
          image: your-registry/sliples-backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              value: postgresql://$(DB_USER):$(DB_PASSWORD)@sliples-postgres-svc:5432/sliples
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: sliples-db-credentials
                  key: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: sliples-db-credentials
                  key: password
            - name: REDIS_URL
              value: redis://sliples-redis-svc:6379/0
            - name: S3_ENDPOINT
              value: https://s3.amazonaws.com
            - name: S3_BUCKET
              value: sliples-screenshots
            - name: S3_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: sliples-s3-credentials
                  key: access-key
            - name: S3_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: sliples-s3-credentials
                  key: secret-key
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: sliples-jwt-secret
                  key: secret
            - name: GOOGLE_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: sliples-google-oauth
                  key: client-id
            - name: GOOGLE_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: sliples-google-oauth
                  key: client-secret
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: sliples-backend-svc
  namespace: sliples
spec:
  selector:
    app: sliples-backend
  ports:
    - port: 8000
      targetPort: 8000
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: sliples-api
  namespace: sliples
spec:
  host: api.sliples.apps.example.com
  to:
    kind: Service
    name: sliples-backend-svc
  port:
    targetPort: 8000
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

#### Worker Deployment

```yaml
# openshift/worker/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sliples-worker
  namespace: sliples
spec:
  replicas: 3  # Scalable
  selector:
    matchLabels:
      app: sliples-worker
  template:
    metadata:
      labels:
        app: sliples-worker
    spec:
      containers:
        - name: worker
          image: your-registry/sliples-backend:latest
          command: ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
          env:
            # Same environment variables as backend
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
```

### Deployment Commands

```bash
# Apply all manifests
oc apply -f openshift/

# Or apply individually
oc apply -f openshift/postgres/
oc apply -f openshift/redis/
oc apply -f openshift/backend/
oc apply -f openshift/worker/
oc apply -f openshift/frontend/

# Check deployment status
oc get pods -n sliples
oc get routes -n sliples

# View logs
oc logs -f deployment/sliples-backend -n sliples
oc logs -f deployment/sliples-worker -n sliples

# Scale workers
oc scale deployment/sliples-worker --replicas=5 -n sliples
```

---

## Environment Variables Reference

### Backend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://sliples:sliples_dev@localhost:5432/sliples` | Yes |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` | Yes |
| `S3_ENDPOINT` | S3/MinIO endpoint URL | `http://localhost:9000` | Yes |
| `S3_BUCKET` | S3 bucket for screenshots | `sliples-screenshots` | Yes |
| `S3_ACCESS_KEY` | S3 access key | `sliples` | Yes |
| `S3_SECRET_KEY` | S3 secret key | `sliples_dev` | Yes |
| `SECRET_KEY` | Application secret key | `change-this-in-production` | Yes (production) |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `http://localhost:5173` | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID | - | For SSO |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret | - | For SSO |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/api/v1/auth/google/callback` | For SSO |
| `ALLOWED_WORKSPACE_DOMAINS` | Allowed Google Workspace domains | - | For SSO |
| `JWT_SECRET_KEY` | JWT signing key | `jwt-secret-change-in-production` | Yes (production) |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `JWT_EXPIRY_HOURS` | JWT token expiry | `24` | No |
| `FRONTEND_URL` | Frontend URL for redirects | `http://localhost:5173` | Yes |
| `BROWSER_CHROME_URL` | Chrome browser WebSocket URL | `ws://browser-chrome:3000` | Yes |
| `BROWSER_FIREFOX_URL` | Firefox browser WebSocket URL | `ws://browser-firefox:3000` | Yes |
| `RETENTION_DAYS` | Default data retention period | `365` | No |
| `SMTP_HOST` | SMTP server host | - | For email |
| `SMTP_PORT` | SMTP server port | `587` | For email |
| `SMTP_USER` | SMTP username | - | For email |
| `SMTP_PASSWORD` | SMTP password | - | For email |
| `EMAIL_FROM` | Sender email address | - | For email |

### Frontend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |

### Worker Configuration

Workers use the same environment variables as the backend, plus:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CELERY_CONCURRENCY` | Number of concurrent workers | `4` | No |

---

## Scaling Considerations

### Horizontal Scaling

#### Backend API
- **Stateless:** Can scale horizontally
- **Recommended:** 2+ replicas for high availability
- **Load balancing:** Use OpenShift Service/Route

#### Celery Workers
- **Scalable:** Add more replicas for more concurrent tests
- **Capacity:** Each worker with `concurrency=4` handles 4 parallel tests
- **Formula:** `max_concurrent_tests = replicas * concurrency`

For 10 concurrent tests:
```bash
# 3 workers * 4 concurrency = 12 capacity
oc scale deployment/sliples-worker --replicas=3
```

#### Browser Containers
- **Limitation:** Single browser type per container
- **Scaling:** Add more browser containers for more parallel tests
- **Memory:** Each browser needs ~2GB shared memory

### Vertical Scaling

#### PostgreSQL
- **CPU:** Increase for complex queries
- **Memory:** Increase for caching
- **Storage:** Monitor and expand PVC as needed

#### Redis
- **Memory:** Size based on job queue length
- **Typical:** 256MB-1GB sufficient for most loads

#### Workers
- **Memory:** 512MB-2GB per worker
- **CPU:** 0.25-1 core per worker

### Performance Tuning

```yaml
# Backend - increase for high traffic
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# Worker - increase for parallel tests
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"

# Browser - needs significant memory
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

---

## Security Configuration

### Network Security

1. **Internal Services:** Only expose backend and frontend externally
2. **Database:** Never expose directly; use internal service names
3. **Redis:** Internal only; no authentication in development
4. **MinIO/S3:** Use signed URLs for screenshot access

### Secrets Management

```bash
# OpenShift Secrets
oc create secret generic sliples-secrets \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=jwt-secret=$(openssl rand -hex 32)
```

### TLS Configuration

```yaml
# Route with TLS
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: sliples-api
spec:
  host: api.sliples.example.com
  to:
    kind: Service
    name: sliples-backend-svc
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
    certificate: |
      -----BEGIN CERTIFICATE-----
      ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      ...
      -----END PRIVATE KEY-----
```

### API Key Security

- Keys are hashed with bcrypt (12 rounds)
- Only key prefix stored in plaintext
- Full key shown only once on creation
- Support for environment-scoped keys

### Google Workspace SSO

1. Create OAuth2 credentials in Google Cloud Console
2. Set authorized redirect URI: `https://api.sliples.example.com/api/v1/auth/google/callback`
3. Configure allowed workspace domains to restrict access

---

## Monitoring and Logging

### Health Checks

```bash
# Kubernetes/OpenShift probes
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Logging

Backend uses structured JSON logging:

```python
# app/main.py configures logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

View logs:
```bash
# Docker Compose
docker compose logs -f backend worker

# OpenShift
oc logs -f deployment/sliples-backend
oc logs -f deployment/sliples-worker
```

### Metrics

Prometheus metrics available at `/metrics` (if enabled):

- `sliples_runs_total` - Total test runs
- `sliples_runs_duration_seconds` - Run duration histogram
- `sliples_active_sessions` - Active interactive sessions

### Alerting

Set up alerts for:
- Health check failures
- High error rates
- Long queue times
- Worker crashes

---

## Backup and Recovery

### Database Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U sliples sliples > backup.sql

# OpenShift
oc exec $(oc get pods -l app=sliples-postgres -o name) -- \
  pg_dump -U sliples sliples > backup.sql
```

### Database Restore

```bash
# Docker Compose
cat backup.sql | docker compose exec -T postgres psql -U sliples sliples

# OpenShift
cat backup.sql | oc exec -i $(oc get pods -l app=sliples-postgres -o name) -- \
  psql -U sliples sliples
```

### Screenshot Backup

Screenshots are stored in S3/MinIO. Use S3 lifecycle policies or sync to backup:

```bash
# Sync to backup bucket
aws s3 sync s3://sliples-screenshots s3://sliples-screenshots-backup
```

### Disaster Recovery

1. **Database:** Regular pg_dump backups, point-in-time recovery if using managed PostgreSQL
2. **Screenshots:** S3 bucket replication or regular sync
3. **Configuration:** Store all configuration in version control
4. **Secrets:** Use secret management solution with backup

### Recovery Procedure

1. Deploy infrastructure from manifests
2. Restore database from backup
3. Verify S3 bucket accessibility
4. Create initial admin API key if needed
5. Verify health endpoint
6. Test basic functionality

---

## Upgrade Procedures

### Rolling Updates

```bash
# Docker Compose
docker compose pull
docker compose up -d

# OpenShift
oc set image deployment/sliples-backend backend=your-registry/sliples-backend:v2.0.0
oc rollout status deployment/sliples-backend
```

### Database Migrations

```bash
# Always run migrations during upgrades
docker compose exec backend alembic upgrade head

# OpenShift
oc exec $(oc get pods -l app=sliples-backend -o name | head -1) -- \
  alembic upgrade head
```

### Rollback

```bash
# Docker Compose - use previous image tag
docker compose down
# Edit docker-compose.yml to previous version
docker compose up -d

# OpenShift
oc rollout undo deployment/sliples-backend
```
