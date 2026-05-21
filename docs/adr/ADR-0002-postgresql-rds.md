# ADR-0002: PostgreSQL em RDS

## Status

Aceita.

## Decisão

Usar PostgreSQL gerenciado em RDS para persistência principal.

## Consequências

- Reduz operação manual de banco.
- Mantém consistência transacional para clientes, veículos e ordens de serviço.
- Exige configuração segura de subnets privadas e security groups.
