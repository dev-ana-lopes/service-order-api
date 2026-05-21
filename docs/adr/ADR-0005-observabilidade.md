# ADR-0005: Observabilidade

## Status

Aceita.

## Decisão

Expor métricas da aplicação, correlation id e instrumentação OpenTelemetry configurável para Datadog e Grafana.

## Consequências

- Facilita demonstração de saúde e comportamento da API.
- Mantém tracing opcional por variável de ambiente.
- Evita dependência obrigatória de stack completa de observabilidade para rodar localmente.
