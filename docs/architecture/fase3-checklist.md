# Checklist da Fase 3

Este arquivo é o ponto canônico para a checklist da Fase 3. O histórico detalhado permanece em `docs/checklists/fase3-checklist.md`.

## Validação técnica

- API FastAPI versionada e testada.
- Autenticação de cliente por JWT emitido pela Lambda.
- Healthchecks `/health` e `/health/ready`.
- Métricas da aplicação em `/metrics`, com visualização em Datadog/Grafana.
- Correlation id gerado ou propagado por requisição.
- Manifests Kubernetes renderizados com imagem GHCR explícita.
- RDS PostgreSQL isolado em subnets privadas.
- CI/CD com lint, testes, build de imagem e deploy controlado.

## Demonstração

- Provisionar k3s em EC2.
- Provisionar RDS PostgreSQL.
- Publicar imagem `ghcr.io/<owner>/service-order-api:sha-<commit>`.
- Aplicar manifests renderizados no k3s.
- Publicar Lambda e API Gateway.
- Chamar `POST /auth/cpf`.
- Usar o Bearer Token na API protegida.
- Mostrar logs, healthchecks e métricas.
