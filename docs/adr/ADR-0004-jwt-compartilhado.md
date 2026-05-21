# ADR-0004: JWT Compartilhado

## Status

Aceita.

## Decisão

A Lambda emite JWT de cliente assinado com secret compartilhado, e a FastAPI valida o token nas rotas protegidas.

## Consequências

- Simplifica a integração entre autenticação serverless e backend monolítico.
- Exige rotação coordenada de `CUSTOMER_JWT_SECRET`.
- Evita consulta síncrona à Lambda em cada requisição da API.
