# Postman

Arquivos:

- `ServiceOrderAPI.postman_collection.json`
- `ServiceOrderAPI.local.postman_environment.json`

## Escopo da collection

A collection agora espelha as rotas atuais do codigo e cobre:

- `Health`: `/health`, `/health/live`, `/health/ready`
- `Auth`: `/auth/register`, `/auth/login`, `/auth/token`
- `Customers`: create, list, detail, update e delete
- `Vehicles`: create, list, detail, update e delete
- `Catalog`: services e parts com create, list, detail, update e delete
- `Service Orders`: abertura por IDs, abertura inline, listagens, detalhe, status, aprovacao manual e atualizacao de status
- `MailHog E2E`: fluxo local automatico para extrair links/tokens do email e validar a recusa do orcamento ponta a ponta
- `Public`: status publico e fluxo manual por token para aprovacao e recusa
- `Metrics`: `/metrics/average-execution-time`

## Como usar

1. Suba o ambiente local com `docker compose --env-file .env up -d --build`.
2. Importe a collection e o environment local.
3. Ajuste apenas `base_url` e `mailhog_url` se o stack estiver em portas diferentes.
4. Rode a sequencia recomendada no Runner:
   `Health -> Auth -> Customers -> Vehicles -> Catalog -> Service Orders -> MailHog E2E -> Metrics`
5. Use a pasta `Public` de forma manual/opcional quando quiser testar tokens preenchendo `approval_token`.
6. Se quiser executar os `DELETE`, altere `run_cleanup=true` no environment.

## O que a collection automatiza

- gera `run_id`, emails, CPF/CNPJ, nomes e placas unicos por execucao
- salva `access_token` e `token_type` apos login/token
- salva `customer_id`, `vehicle_id`, `service_id`, `part_id`, `service_order_id` e `inline_service_order_id`
- limpa IDs e tokens gerados automaticamente no inicio de uma nova execucao
- consulta o MailHog local, encontra o email da OS inline e extrai `approve_url`, `reject_url`, `approve_token` e `reject_token`
- deixa os requests de cleanup desativados por padrao para nao quebrar o fluxo principal

## Fluxo manual vs fluxo automatico

### Fluxo automatico com MailHog

A pasta `MailHog E2E` e a demonstracao oficial local do fluxo de email:

1. cria uma OS inline com `mailhog_customer_email`
2. consulta `GET {{mailhog_url}}/api/v2/messages`
3. identifica a mensagem correta pelo destinatario e pelo `service_order_id`
4. extrai os links e tokens do email
5. chama `POST /public/service-orders/{id}/approval` com o `reject_token`
6. valida que a OS ficou em `DIAGNOSIS` com `approval_decision=REJECTED`

### Fluxo manual com `approval_token`

A pasta `Public` continua compativel com uso manual:

- `GET /public/service-orders/{{service_order_id}}/approval` espera um token de aprovacao valido em `approval_token` e valida `decision=APPROVED` com `status=IN_PROGRESS`
- `POST /public/service-orders/{{service_order_id}}/approval` espera um token de recusa valido em `approval_token` e valida `decision=REJECTED` com `status=DIAGNOSIS`
- `GET /public/service-orders/{{service_order_id}}/status` valida os campos `status`, `approval_decision` e `rejection_reason`

## Variaveis principais do environment local

- `base_url`: URL da API local
- `mailhog_url`: URL do MailHog local
- `approval_token`: token manual para a pasta `Public`
- `approve_token` e `reject_token`: tokens preenchidos automaticamente pela pasta `MailHog E2E`
- `approve_url` e `reject_url`: links extraidos automaticamente do email
- `run_cleanup`: controla se os requests `DELETE` executam ou sao pulados

O Swagger em `/docs` e a collection usam as mesmas rotas atuais do projeto.
