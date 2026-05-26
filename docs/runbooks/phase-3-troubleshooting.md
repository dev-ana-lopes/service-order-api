# Phase 3 Troubleshooting

This file captures issues already found during the AWS Academy/k3s delivery.

## Invalid CORS_ALLOWED_ORIGINS

Symptom: application startup or request handling fails because the value cannot
be parsed.

Fix: use a parser-compatible value in `APP_ENV`, for example:

```dotenv
CORS_ALLOWED_ORIGINS=http://32.197.10.136
```

Use one URL per expected parser format. Avoid free-form text or unescaped lists.

## TRUSTED_HOSTS Returning 400 on Probes

Symptom: `/health` or `/health/ready` returns `400 Bad Request` from probes or
API Gateway because the host header does not match.

Fix for the academic demo:

```dotenv
TRUSTED_HOSTS=*
```

For production, restrict this after the final domain/API Gateway hostnames are
known.

## OTEL Endpoint Not Validated

Symptom: traces fail or the API attempts to export spans before the Datadog
Agent OTLP HTTP receiver is validated.

Fix: keep tracing disabled for the current delivery:

```dotenv
OTEL_ENABLED=false
DD_TRACE_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
```

Before enabling traces, confirm the Datadog Agent service in the `datadog`
namespace exposes port `4318`:

```bash
kubectl get svc -n datadog
kubectl describe svc -n datadog datadog-agent
```

The current delivery validates Datadog logs, Kubernetes/container visibility
and Synthetic Monitoring, not OTLP traces.

## DATABASE_URL ssl=require vs sslmode=require

Symptom: runtime or migration fails depending on the driver.

Fix:

- API runtime: `postgresql+asyncpg://...?ssl=require`
- Alembic/migration: `postgresql://...?sslmode=require`

The GitHub Actions deploy workflow reads the API secret and creates a separate
migration secret with the converted value.

## Ingress Path /api vs /

Symptom: API Gateway calls fail or return 404 because the backend path is not
aligned with Traefik.

Fix: for the current API Gateway proxy integration, Traefik/Ingress must accept
the root path `/`. The workflow patches the rendered ingress path to `/` during
deployment.

## API Gateway Integration Path

Symptom: public API Gateway URL is reachable but backend routes return 404 or
integration errors.

Fix: configure the HTTP API integration as:

```text
http://32.197.10.136/{proxy}
```

The validated public URL is:

```text
https://oubv5hamu5.execute-api.us-east-1.amazonaws.com
```
