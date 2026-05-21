# ADR-0003: API Gateway com Lambda Auth

## Status

Aceita.

## Decisão

Expor autenticação por CPF via API Gateway HTTP API integrado a uma Lambda dedicada.

## Consequências

- Isola o fluxo serverless de autenticação.
- Permite demonstrar integração entre API Gateway, Lambda e RDS.
- A API principal continua no k3s.
