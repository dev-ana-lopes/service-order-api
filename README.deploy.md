# Deployment Runbooks

⚠️ **IMPORTANT:** Kubernetes is the **PRIMARY** production deployment path. This document covers the **LEGACY FALLBACK** with Docker Compose.

---

## Primary Deployment: Kubernetes

**Status:** Active, automated via CI/CD  
**Target:** k3s (single-node K3s on EC2)  
**Automation:** GitHub Actions workflow  

For the primary production deployment procedure, see [README.md#kubernetes](README.md#kubernetes) and [README.md#cicd-pipeline](README.md#cicd-pipeline).

The Kubernetes deployment is:
- Fully automated via GitHub Actions
- Image built/published in GHCR
- `kubectl` commands executed remotely inside the EC2 host (k3s) via SSH
- Deployed to Kubernetes manifests (namespace, ConfigMap, Secret, migration job, deployment, service, HPA)
- Monitored with liveness/readiness probes and autoscaling
- Documented in the main README with step-by-step manual deploy instructions if needed

### CI/CD Requirements for Primary Kubernetes Deploy

GitHub Environment `production` must provide:

- Secret `APP_ENV_PROD`
- Secret `EC2_SSH_KEY`
- Variable `EC2_HOST`
- Variable `EC2_USER`
- Optional variable `EC2_PORT` (default `22`)

---

## Fallback: Legacy Docker Compose Deployment

**Status:** Deprecated, preserved for emergency use only  
**Target:** EC2 with Docker Compose  
**Automation:** Manual procedure (not automated in CI/CD)  

### When to Use Fallback

1. **Emergency recovery** of an older Compose-based environment
2. **Operational comparison** between K8s and Compose deployments
3. **Team request** to demonstrate the legacy flow
4. **Local development** (see [README.md#how-to-run-locally](README.md#how-to-run-locally))

### Prerequisites

- EC2 Linux instance with Docker and Docker Compose v2
- PostgreSQL instance accessible from the EC2 host
- Security group with port `8000` open (if exposing the Compose service)
- `.env.prod` file created from `.env.prod.example` template

### Required Environment Variables

Copy and configure:

```bash
cp .env.prod.example .env.prod
python3 scripts/deploy/prepare_env.py .env.prod
```

**Mandatory fields:**
- `DATABASE_URL` (PostgreSQL connection string)
- `APP_BASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `TRUSTED_HOSTS`
- `JWT_SECRET` or `JWT_SECRET_FILE`
- `APPROVAL_TOKEN_SECRET` or `APPROVAL_TOKEN_SECRET_FILE`

**Optional (if using SMTP):**
- `EMAIL_PROVIDER=SMTP`
- `SMTP_HOST`, `SMTP_FROM_EMAIL`
- `SMTP_USERNAME`, `SMTP_PASSWORD`

### Deployment Steps

#### 1. Prepare the Host (One-Time Setup)

```bash
chmod +x scripts/deploy/bootstrap_ec2.sh
./scripts/deploy/bootstrap_ec2.sh
```

This installs Docker and Docker Compose v2 on the EC2 instance.

#### 2. Prepare the Environment

```bash
python3 scripts/deploy/prepare_env.py .env.prod
```

This validates all required fields and normalizes the `.env.prod` file.

#### 3. Build and Deploy

```bash
chmod +x scripts/deploy/release.sh
API_IMAGE=service-order-api:prod ./scripts/deploy/release.sh
```

This script:
- Builds the Docker image locally on the EC2 host
- Runs database migrations (Alembic upgrade)
- Starts the API service with `docker compose up -d api`

#### 4. Verify Deployment

```bash
curl http://<host>:8000/health
curl http://<host>:8000/health/ready
curl http://<host>:8000/docs
```

### Deployment Pipeline (Docker Compose)

```
.env.prod (secrets)
    ↓
prepare_env.py (validation)
    ↓
docker build (local image: service-order-api:prod)
    ↓
docker compose run migrate (Alembic upgrade)
    ↓
docker compose up -d api (start API service)
    ↓
curl /health/ready (verify readiness)
```

### Monitoring & Logs

View running containers:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f api
```

Stop services:

```bash
docker compose down
```

### Notes on Migration

- The legacy Compose flow uses the same `scripts/deploy/prepare_env.py` validation script for consistency
- The same database schema applies to both Kubernetes and Compose deployments
- The transition from Compose to Kubernetes is one-way for production; fallback only for recovery

---

## Transición recomendada (Legacy, No Longer Active)

- usar o fallback Compose apenas enquanto necessário;
- manter novas demonstrações e documentação centradas no fluxo `k3s`;
- desligar a porta `8000` no Terraform quando o fallback não for mais necessário.
