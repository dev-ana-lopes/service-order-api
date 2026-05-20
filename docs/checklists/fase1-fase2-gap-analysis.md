# Gap Analysis Fase 1 e Fase 2

| Requisito | Status | Evidência | Ação |
| --- | --- | --- | --- |
| Clean Architecture com camadas `domain/application/infrastructure/presentation` | Implementado | `src/domain`, `src/application`, `src/infrastructure`, `src/presentation` | Manter disciplina de dependências |
| Agregado principal `ServiceOrder` | Implementado | `src/domain/entities/service_order.py` | Continuar centralizando regras de status no domínio |
| Autenticação JWT | Implementado | `src/presentation/api/routes/auth_routes.py`, `src/infrastructure/email/jwt_service.py` | Rotacionar segredos no ambiente real |
| CRUD de clientes | Implementado | `src/presentation/api/routes/customer_routes.py` | Sem ação imediata |
| CRUD de veículos | Implementado | `src/presentation/api/routes/vehicle_routes.py` | Sem ação imediata |
| CRUD de catálogo de serviços | Implementado | `src/presentation/api/routes/catalog_routes.py` | Sem ação imediata |
| CRUD de peças/estoque | Implementado | `src/presentation/api/routes/catalog_routes.py` | Sem ação imediata |
| Validação de CPF/CNPJ | Implementado | `src/domain/validation/br_documents.py`, `src/presentation/schemas/admin_schema.py` | Sem ação imediata |
| Validação de placa | Implementado | `src/domain/validation/br_documents.py`, `src/presentation/schemas/admin_schema.py` | Sem ação imediata |
| Criação de OS | Implementado | `CreateServiceOrderUseCase`, `POST /service-orders` | Sem ação imediata |
| Cálculo automático de orçamento | Implementado | `ServiceOrder.budget_total`, `tests/test_service_order_api.py` | Sem ação imediata |
| Redução de estoque | Implementado | `CreateServiceOrderUseCase`, `MockInventoryPartRepository.decrease_stock` coberto em testes | Sem ação imediata |
| Aprovação/reprovação administrativa | Implementado | `POST /service-orders/{id}/approval` | Sem ação imediata |
| Aprovação pública por token | Implementado | `src/presentation/api/routes/public_routes.py` | Sem ação imediata |
| Listagem ativa com prioridade | Implementado | `GET /service-orders/active`, `tests/test_domain_rules.py` | Sem ação imediata |
| Métrica de tempo médio de execução | Implementado | `GET /metrics/average-execution-time` | Sem ação imediata |
| PostgreSQL + Alembic | Implementado | `alembic/`, `src/infrastructure/database/` | Sem ação imediata |
| Docker Compose local | Implementado | `docker-compose.yml` | Sem ação imediata |
| SMTP local com MailHog | Implementado | `docker-compose.yml`, `SMTP_HOST=mailhog` | Sem ação imediata |
| SMTP real em produção | Parcial | `.env.prod.example` e validação em `Settings` exigem provedor real | Configurar SES/SMTP no ambiente |
| Deploy automatizado em produção | Parcial | workflow `deploy-ec2` e scripts `scripts/deploy/*` | Preencher segredos do GitHub e preparar host |
| Pipeline com lint, testes e cobertura | Implementado | `.github/workflows/ci-cd.yml` | Sem ação imediata |
| Publicação opcional em registry | Implementado | job `publish-image` | Provisionar ECR e credenciais |
| IaC simples para AWS | Implementado | `infra/` com VPC opcional, EC2, SGs e RDS | Ajustar `terraform.tfvars` do ambiente |
| Kubernetes como trilha evolutiva | Implementado | `k8s/` | Aplicar somente se houver maturidade operacional |
| Healthcheck, readiness e liveness | Implementado | `/health`, `/health/live`, `/health/ready` | Integrar com monitoramento da plataforma |
| Logging estruturado | Implementado | `src/infrastructure/logging.py` | Enviar stdout para CloudWatch/ELK |
| Estratégia de segredos para produção | Implementado | suporte `*_FILE`, `.gitignore`, `README.deploy.md` | Evoluir para SSM/Secrets Manager |
| Segurança operacional documentada | Implementado | `README.deploy.md`, `docs/runbooks/troubleshooting.md` | Revisar periodicamente |
| Evidências de testes dos fluxos críticos | Implementado | `tests/test_service_order_api.py`, `tests/test_auth_and_admin_api.py`, `tests/test_settings_and_health.py` | Expandir integração real com banco se necessário |
| Dependências de laboratório/AWS Academy | Depende de ambiente | ECR, EC2, RDS, SMTP real e acesso SSH | Provisionar recursos disponíveis no lab |
