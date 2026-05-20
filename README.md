# service-order-api

API principal FastAPI da Fase 3 do Tech Challenge FIAP.

## Propósito
- executar a aplicação principal em Kubernetes;
- aceitar JWT administrativo e JWT de cliente emitido pela Lambda;
- proteger rotas de OS com autorização contextual;
- expor healthchecks, métricas Prometheus e traces OpenTelemetry.

## Stack
- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Kubernetes/k3s
- OpenTelemetry
- Datadog com apoio Prometheus/Grafana

## Execução local
```bash
make compose-up
make compose-smoke
make test
```

## Endpoints mínimos
- `POST /service-orders`
- `GET /service-orders/{id}/status`
- `GET /service-orders/active`
- `POST /service-orders/{id}/approval`
- `GET /health`
- `GET /health/ready`
- `GET /metrics`
- `GET /docs`

## Variáveis principais
- `DATABASE_URL`
- `JWT_SECRET`
- `CUSTOMER_JWT_SECRET`
- `CUSTOMER_JWT_ISSUER`
- `DD_SERVICE`
- `DD_ENV`
- `DD_VERSION`
- `OTEL_EXPORTER_OTLP_ENDPOINT`

## Kubernetes
O repositório mantém `Deployment`, `Service`, `Ingress`, `ConfigMap`, `Secret`, `HPA` e `Job` de migration.

## CI/CD
- PR: lint, tests, coverage, render de manifests
- `homolog`: build/push GHCR e deploy homolog
- `main`: build/push GHCR e deploy produção

## Repositórios da Fase 3
- [service-order-api](/mnt/c/service-order-api)
- [service-order-auth-lambda](/mnt/c/service-order-auth-lambda)
- [service-order-infra-k8s](/mnt/c/service-order-infra-k8s)
- [service-order-infra-db](/mnt/c/service-order-infra-db)

## Governança
- adicionar o usuário `soat-architecture` em todos os quatro repositórios;
- proteger `main` e `homolog`;
- bloquear commit direto;
- exigir PR e environment para deploy.

## Swagger/Postman
- Swagger local: `http://localhost:8000/docs`
- Collection base: `docs/postman/ServiceOrderAPI.postman_collection.json`

## Diagramas
- [component-diagram.md](/mnt/c/service-order-api/docs/architecture/component-diagram.md)
- [sequence-auth-and-open-service-order.md](/mnt/c/service-order-api/docs/architecture/sequence-auth-and-open-service-order.md)
- [database-er.md](/mnt/c/service-order-api/docs/architecture/database-er.md)
