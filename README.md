# service-order-api

Main FastAPI application for the Phase 3 service order platform.

## Current Demo State

- Public API Gateway URL: `https://oubv5hamu5.execute-api.us-east-1.amazonaws.com`
- Runtime: k3s on EC2, with API Gateway HTTP API proxying to `http://32.197.10.136/{proxy}`.
- Database: PostgreSQL on AWS RDS.
- Image registry: GHCR, using tags such as `ghcr.io/<owner>/service-order-api:sha-<commit>`.
- Observability: Datadog is the official tool for Phase 3.

Validated public endpoints through API Gateway:

- `GET /health`
- `GET /health/ready`
- `GET /docs`
- `GET /metrics`

## Purpose

- Manage customers, vehicles, services, parts and service orders.
- Accept administrative JWTs signed with `JWT_SECRET`.
- Accept customer JWTs issued by the CPF authentication Lambda.
- Expose health/readiness endpoints, JSON request logs with correlation identifiers and application metrics.
- Support the k3s + EC2 + RDS + GHCR deployment path used in the demo.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL/RDS
- Alembic
- Docker/GHCR
- Kubernetes/k3s on EC2
- GitHub Actions
- Datadog

## Local Development

```bash
uv sync --dev
make compose-up
make test
```

Useful local endpoints:

- `http://localhost:8000/health`
- `http://localhost:8000/health/ready`
- `http://localhost:8000/docs`
- `http://localhost:8000/metrics`

## Main Endpoints

- `POST /service-orders`
- `GET /service-orders/{id}/status`
- `GET /service-orders/active`
- `POST /service-orders/{id}/approval`
- `GET /health`
- `GET /health/ready`
- `GET /docs`
- `GET /metrics`
- `GET /metrics/average-execution-time`

## Customer Authentication Lambda

Customer authentication by CPF is handled by the `service-order-auth-lambda`
repository through the AWS Lambda `service-order-auth-cpf`.

The public route is exposed through API Gateway:

`POST /auth/cpf`

The API validates customer JWTs issued by that Lambda using:

- `CUSTOMER_JWT_SECRET`
- `CUSTOMER_JWT_ISSUER`
- `CUSTOMER_JWT_ALGORITHM`

Operational details such as Lambda runtime, package zip, VPC config and manual
upload are documented in the `service-order-auth-lambda` repository.

## Production Environment Notes

`APP_ENV` in GitHub Actions must be configured as a secret and must not be
committed. The production file should include values equivalent to:

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/service_order_db?ssl=require
CORS_ALLOWED_ORIGINS=http://32.197.10.136
TRUSTED_HOSTS=*
OTEL_ENABLED=false
DD_TRACE_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
DD_SERVICE=service-order-api
DD_ENV=production
DD_VERSION=3.0.0
```

Important details:

- API runtime uses SQLAlchemy asyncpg, so the application URL uses
  `postgresql+asyncpg://...?ssl=require`.
- Alembic/migration jobs use the sync PostgreSQL driver behavior, so the deploy
  workflow converts the migration URL to `sslmode=require`.
- `OTEL_ENABLED=false`, `DD_TRACE_ENABLED=false` and an empty
  `OTEL_EXPORTER_OTLP_ENDPOINT` must remain in production for the current
  delivery.
- `CUSTOMER_JWT_SECRET` must match the value used by
  `service-order-auth-lambda`.
- `TRUSTED_HOSTS=*` is accepted for the academic demo because API Gateway and
  Traefik health probes use different host headers. Tighten it in production.

## Observability

Datadog is the official observability tool for Phase 3. The Datadog Agent was
installed via Helm in the `datadog` namespace.

Current coverage:

- Kubernetes container logs collected in Datadog.
- `service-order-api` JSON logs with `correlation_id`, `request_id`, `method`,
  `path`, `status_code`, `duration_ms`, `service`, `env` and `version`.
- Datadog Synthetic Test for `/health/ready` through API Gateway.
- Datadog dashboard with API requests by status code, 4xx/5xx errors, requests
  by path, readiness response time, EC2 CPU usage, EC2 memory used, running API
  pods and successful API requests.
- Kubernetes HPA evidence for CPU-based scaling between 2 and 5 pods.

Prometheus/Grafana is not the active observability stack for this delivery. It
was evaluated and removed because of AWS Academy EC2 resource limits. The
`/metrics` endpoint remains available as a technical application endpoint.

Tracing and OTLP/APM are not active in this repository:

- `OTEL_ENABLED=false`
- `DD_TRACE_ENABLED=false`
- `OTEL_EXPORTER_OTLP_ENDPOINT=`

## Kubernetes

The repository contains Kubernetes manifests for namespace, ConfigMap, Secret
template, migration Job, Deployment, Service, Ingress and HPA.

The HPA must remain configured as:

- `minReplicas: 2`
- `maxReplicas: 5`
- CPU `averageUtilization: 70`

Manifests must be rendered with an explicit GHCR image before applying:

```bash
python3 scripts/deploy/prepare_env.py <env-file>
python3 scripts/deploy/render_k8s_manifests.py \
  --env-file <env-file> \
  --output-dir <dir> \
  --image ghcr.io/<owner>/service-order-api:sha-<commit>
```

Never apply manifests containing `__API_IMAGE__` or `${API_IMAGE}`.

## CI/CD

The GitHub Actions workflow for this repository is scoped to the API:

- checkout
- Python 3.12 setup
- uv setup and `uv sync --locked --dev`
- lint
- tests with coverage
- rendered manifest validation
- Docker build
- GHCR push
- k3s deployment via SSH
- migration job
- rollout validation
- public smoke test

Lambda packaging, Lambda deployment and Terraform for the CPF authentication
Lambda belong to the `service-order-auth-lambda` repository.

## Documentation

- `README.deploy.md`
- `docs/runbooks/k3s-github-actions-deploy.md`
- `docs/runbooks/phase-3-troubleshooting.md`
- `docs/observability/observability-plan.md`
- `docs/observability/datadog-runbook.md`
- `docs/delivery/phase-3-checklist.md`
- `docs/architecture/component-diagram.md`
- `docs/architecture/auth-sequence.md`
- `docs/architecture/service-order-sequence.md`

## Safety Rules

- Do not commit `.env`, `.env.prod` or real secrets.
- Do not commit `build/`, `review/`, `*.tfstate`, `*.tfvars` or Lambda Terraform files.
- Do not deploy local Docker images to k3s.
- Do not run `terraform apply` from this repository.
- Keep Kubernetes as the primary demo path and Docker Compose as fallback only.
