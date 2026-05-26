# RFC-0004: Observabilidade

## Proposta

Padronizar a observabilidade da entrega atual em Datadog, cobrindo logs de
containers, logs JSON com correlation id/request id, visibilidade Kubernetes,
dashboards/monitores e Synthetic Monitoring para health/readiness via API
Gateway.

## Motivacao

Permitir diagnostico da demo em uma ferramenta unica e ja escolhida para a
entrega, sem habilitar traces OTLP antes de validar a porta `4318` no Agent.
