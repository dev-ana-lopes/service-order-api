# Event Storming e Domain Storytelling

## Leitura do documento

Este arquivo consolida os casos de uso do repositório em duas visões:

- `event storming`: ator, comando, regra, evento e leitura impactada;
- `domain storytelling`: narrativa do que cada ator faz e do que o sistema responde.

## Event storming

### Autenticação

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Registrar usuário | Administrador | `POST /auth/register` | e-mail deve ser único | `UserRegistered` | login passa a aceitar o novo usuário |
| Autenticar usuário | Administrador | `POST /auth/login` ou `POST /auth/token` | credenciais devem ser válidas | `UserAuthenticated` | token JWT liberado para APIs autenticadas |

### Clientes

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Criar cliente | Administrador | `POST /customers` | CPF/CNPJ e e-mail não podem conflitar | `CustomerCreated` | listagem e detalhe de clientes |
| Listar clientes | Administrador | `GET /customers` | consulta autenticada | `CustomersListed` | grid administrativo |
| Consultar cliente | Administrador | `GET /customers/{id}` | cliente deve existir | `CustomerRead` | tela de detalhe |
| Atualizar cliente | Administrador | `PUT /customers/{id}` | não pode gerar conflito de CPF/CNPJ ou e-mail | `CustomerUpdated` | detalhe e listagem |
| Excluir cliente | Administrador | `DELETE /customers/{id}` | cliente deve existir | `CustomerDeleted` | listagem administrativa |

### Veículos

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Criar veículo | Administrador | `POST /vehicles` | cliente informado deve existir; placa válida | `VehicleCreated` | listagem e detalhe de veículos |
| Listar veículos | Administrador | `GET /vehicles` | pode filtrar por cliente | `VehiclesListed` | tela administrativa |
| Consultar veículo | Administrador | `GET /vehicles/{id}` | veículo deve existir | `VehicleRead` | detalhe do veículo |
| Atualizar veículo | Administrador | `PUT /vehicles/{id}` | cliente deve existir; placa válida | `VehicleUpdated` | detalhe e listagem |
| Excluir veículo | Administrador | `DELETE /vehicles/{id}` | veículo deve existir | `VehicleDeleted` | listagem administrativa |

### Catálogo de serviços

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Criar serviço de catálogo | Administrador | `POST /catalog/services` | descrição e preço válidos | `CatalogServiceCreated` | consulta do catálogo |
| Listar serviços de catálogo | Administrador | `GET /catalog/services` | consulta autenticada | `CatalogServicesListed` | seleção do orçamento |
| Consultar serviço de catálogo | Administrador | `GET /catalog/services/{id}` | serviço deve existir | `CatalogServiceRead` | detalhe do item |
| Atualizar serviço de catálogo | Administrador | `PUT /catalog/services/{id}` | serviço deve existir | `CatalogServiceUpdated` | catálogo administrativo |
| Excluir serviço de catálogo | Administrador | `DELETE /catalog/services/{id}` | serviço deve existir | `CatalogServiceDeleted` | catálogo administrativo |

### Estoque e peças

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Criar peça de estoque | Administrador | `POST /catalog/parts` | nome não pode duplicar | `InventoryPartCreated` | listagem de peças |
| Listar peças | Administrador | `GET /catalog/parts` | consulta autenticada | `InventoryPartsListed` | orçamento e administração |
| Consultar peça | Administrador | `GET /catalog/parts/{id}` | peça deve existir | `InventoryPartRead` | detalhe da peça |
| Atualizar peça | Administrador | `PUT /catalog/parts/{id}` | não pode gerar conflito de nome | `InventoryPartUpdated` | estoque administrativo |
| Excluir peça | Administrador | `DELETE /catalog/parts/{id}` | peça deve existir | `InventoryPartDeleted` | estoque administrativo |

### Ordens de serviço

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Abrir OS | Administrador | `POST /service-orders` | precisa de serviço; resolve cliente e veículo; calcula orçamento | `ServiceOrderCreated` | detalhe, listagem, status |
| Listar OS | Administrador | `GET /service-orders` | consulta autenticada | `ServiceOrdersListed` | tela geral |
| Listar OS ativas | Administrador | `GET /service-orders/active` | exclui `FINISHED` e `DELIVERED`; ordena por prioridade operacional | `ActiveServiceOrdersListed` | quadro operacional |
| Consultar detalhe da OS | Administrador | `GET /service-orders/{id}` | OS deve existir | `ServiceOrderRead` | detalhe completo |
| Consultar status da OS | Administrador | `GET /service-orders/{id}/status` | OS deve existir | `ServiceOrderStatusRead` | acompanhamento rápido |

### Aprovação e recusa do orçamento

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Enviar orçamento por e-mail | Sistema | criação da OS ou retorno para `WAITING_APPROVAL` | gera token de aprovação e token de recusa | `ApprovalEmailRequested` | MailHog / SMTP |
| Aprovar orçamento manualmente | Administrador | `POST /service-orders/{id}/approval` com `approved=true` | OS deve estar em `WAITING_APPROVAL` | `BudgetApproved` | status da OS vai para `IN_PROGRESS` |
| Recusar orçamento manualmente | Administrador | `POST /service-orders/{id}/approval` com `approved=false` | OS deve estar em `WAITING_APPROVAL` | `BudgetRejected` | OS volta para `DIAGNOSIS` |
| Aprovar orçamento por link | Cliente | `GET /public/service-orders/{id}/approval?token=...` | token válido, não expirado e correspondente à OS | `BudgetApproved` | fluxo público e autenticado |
| Recusar orçamento por link | Cliente | `GET /public/service-orders/{id}/approval?token=...` | token válido, não expirado e correspondente à OS | `BudgetRejected` | fluxo público e autenticado |
| Aprovar ou recusar por notificação externa | Sistema externo | `POST /public/service-orders/{id}/approval` | token válido | `BudgetApproved` ou `BudgetRejected` | status público e interno |
| Consultar status público | Cliente | `GET /public/service-orders/{id}/status` | OS deve existir | `PublicServiceOrderStatusRead` | acompanhamento sem autenticação |

### Atualização manual de status

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Alterar para `WAITING_APPROVAL` | Administrador | `PATCH /service-orders/{id}/status` | transição deve ser válida | `ServiceOrderMovedToWaitingApproval` | novo e-mail de orçamento |
| Alterar para `IN_PROGRESS` | Administrador | `PATCH /service-orders/{id}/status` | transição deve ser válida | `ServiceOrderStarted` | listagem ativa |
| Alterar para `FINISHED` | Administrador | `PATCH /service-orders/{id}/status` | transição deve ser válida | `ServiceOrderFinished` | métricas e status |
| Alterar para `DELIVERED` | Administrador | `PATCH /service-orders/{id}/status` | transição deve ser válida | `ServiceOrderDelivered` | remove da lista ativa |

### Métricas

| Caso | Ator | Comando | Regra de negócio | Evento/resultante | Leitura impactada |
| --- | --- | --- | --- | --- | --- |
| Consultar tempo médio de execução | Administrador | `GET /metrics/average-execution-time` | calcula sobre OS concluídas | `AverageExecutionTimeCalculated` | dashboard e observabilidade |

## Domain storytelling

### 1. Autenticação

O administrador registra um usuário para operar o sistema. O backend valida se o e-mail já existe, persiste o usuário e passa a aceitar login. Depois, o administrador autentica e recebe um JWT para acessar os endpoints protegidos.

### 2. Cadastro de clientes e veículos

O administrador mantém a base cadastral de clientes e veículos. O sistema protege unicidade de CPF/CNPJ, e-mail e associação correta entre cliente e veículo. Essas informações alimentam a abertura da OS e as consultas administrativas.

### 3. Catálogo e estoque

O administrador registra serviços padronizados e peças em estoque. O sistema usa esse catálogo para composição de orçamento e também pode aceitar payload inline legado, preservando compatibilidade com os endpoints existentes.

### 4. Abertura da ordem de serviço

O administrador abre uma nova OS. O sistema resolve ou cria cliente e veículo, consolida serviços e peças, calcula o orçamento e persiste a OS em `WAITING_APPROVAL`. Em seguida, tenta enviar um e-mail com os links de aprovação e recusa. Se SMTP falhar, a OS continua criada, porque o envio é best-effort.

### 5. Aprovação do orçamento

O cliente recebe o orçamento e clica em `Aprovar`, ou um sistema externo envia a decisão usando o token. O backend valida o token, registra `approval_decision=APPROVED`, marca `approval_decision_at` e move a OS para `IN_PROGRESS`. A OS passa a aparecer no fluxo operacional da oficina como execução em andamento.

### 6. Recusa do orçamento

O cliente recebe o mesmo e-mail e clica em `Rejeitar`. O backend valida o token, registra `approval_decision=REJECTED`, marca `approval_decision_at` e devolve a OS para `DIAGNOSIS`.

Esse é o ponto central do domínio:

- a decisão do orçamento fica rejeitada;
- o status operacional volta para a etapa em que a oficina pode revisar o diagnóstico, ajustar valores e reenviar o orçamento;
- por isso o sistema não cria `status=REJECTED`.

### 7. Reenvio do orçamento

Depois de revisar o diagnóstico ou alterar itens, o administrador pode mover a OS de volta para `WAITING_APPROVAL`. O sistema reaproveita o fluxo de envio do orçamento e gera novos tokens para aprovação ou recusa.

### 8. Execução, finalização e entrega

Com orçamento aprovado, a OS segue para `IN_PROGRESS`, depois `FINISHED` e finalmente `DELIVERED`. As transições são validadas pela entidade `ServiceOrder`, que protege a ordem do workflow. A listagem ativa deixa de exibir OS finalizadas e entregues.

### 9. Métricas

O administrador consulta o tempo médio de execução das OS concluídas. O sistema usa o repositório de ordens de serviço para gerar a leitura agregada e expor o indicador em endpoint próprio.

## Narrativa completa do fluxo de e-mail com MailHog

1. o administrador cria a OS;
2. a aplicação persiste a OS em `WAITING_APPROVAL`;
3. a aplicação gera dois tokens: aprovação e recusa;
4. o SMTP local entrega a mensagem no MailHog;
5. o cliente abre o e-mail e clica em `Rejeitar`;
6. a rota pública valida o token;
7. a camada de aplicação aplica `approval_decision=REJECTED`;
8. a entidade `ServiceOrder` move a OS para `DIAGNOSIS`;
9. o fluxo público e o fluxo autenticado passam a refletir:
   - `status=DIAGNOSIS`
   - `approval_decision=REJECTED`

## Leituras críticas para validação da banca

- `GET /public/service-orders/{id}/status`
- `GET /service-orders/{id}`
- `GET /service-orders/{id}/status`
- MailHog em `http://localhost:8025`
