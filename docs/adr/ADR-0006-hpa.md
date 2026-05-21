# ADR-0006: HPA

## Status

Aceita.

## Decisão

Configurar HorizontalPodAutoscaler para a FastAPI no k3s.

## Consequências

- Demonstra elasticidade no Kubernetes.
- Depende de métricas de recursos disponíveis no cluster.
- Mantém limites conservadores para custo baixo.
