# Documentação do Sistema CRED-COBR

> Documento de referência técnica e operacional do CRED-COBR. Ele descreve o comportamento implementado no código atual.

## 1. Visão geral

O CRED-COBR é um sistema Django para importar e administrar uma carteira de cobrança. Ele centraliza empresas, clientes, boletos, operações de cobrança, negociações, dashboards, relatórios e notificações.

Os estados operados são CE, BA e PE. No dashboard, empresas Nova e Multi são consolidadas em PE por compartilharem o mesmo estado cadastrado.

### Capacidades principais

- Importação de boletos de planilha Excel, relatório legado e banco SQL legado.
- Consulta e filtragem de carteira por estado, empresa, grupo, operador, situação e vencimento.
- Registro de contatos, promessas de pagamento e acordos parcelados.
- Dashboards estaduais com indicadores e rankings de devedores.
- Relatórios Excel e PDF por estado e faixa de atraso.
- Gestão de usuários própria, com papéis Administrador e Gestor.
- Auditoria de ações relevantes e notificações por e-mail/WhatsApp.
- Processamento assíncrono por Celery e tarefas agendadas por Celery Beat.

## 2. Arquitetura

```text
Navegador / API REST
        │
        ▼
Django (views, DRF, templates)
        │
        ├── PostgreSQL ou SQLite: dados operacionais
        ├── Redis: broker/cache Celery em ambientes configurados
        ├── Celery worker: importações, relatórios e verificações
        ├── Celery Beat: agendamentos diários
        └── SMTP / Meta WhatsApp: entrega de notificações
```

### Estrutura do repositório

| Caminho | Responsabilidade |
| --- | --- |
| `apps/accounts` | Usuários, papéis e gestão de acessos. |
| `apps/companies` | Estados, empresas e grupos econômicos. |
| `apps/customers` | Clientes e seus dados cadastrais. |
| `apps/receivables` | Boletos/títulos a receber e API de consulta. |
| `apps/collections` | Cobrança, contatos, promessas e acordos. |
| `apps/imports` | Normalização e persistência de fontes de dados. |
| `apps/dashboard` | Telas, filtros e indicadores gerenciais. |
| `apps/processing` | Cálculos financeiros e rankings. |
| `apps/reports` | Geração e armazenamento de relatórios. |
| `apps/notifications` | E-mail, WhatsApp e histórico de notificações. |
| `apps/audit` | Registro imutável de ações de negócio. |
| `core` | Configuração Django, Celery, URLs e tarefas globais. |
| `shared` | Modelos e utilitários compartilhados. |
| `templates` / `static` | Interface HTML, CSS e JavaScript. |

## 3. Tecnologias

- Python 3.12+
- Django 5 e Django REST Framework
- PostgreSQL em container ou SQLite no desenvolvimento local
- Celery, Celery Beat e Redis
- Pandas, OpenPyXL e xlrd para importação
- ReportLab e OpenPyXL para relatórios
- Gunicorn para servir a aplicação em container
- Docker Compose para ambiente integrado

## 4. Domínio de dados

### Entidades principais

| Entidade | Descrição |
| --- | --- |
| `User` | Usuário autenticado; possui papel e WhatsApp. |
| `State` | Estado atendido, identificado por código de duas letras. |
| `Company` | Empresa vinculada a um estado. |
| `EconomicGroup` | Grupo econômico ao qual um cliente pode pertencer. |
| `Customer` | Cliente, identificado unicamente pelo código de cliente. |
| `Receivable` | Boleto/título: empresa, cliente, vencimento, valores e situação financeira. |
| `CollectionStatus` | Situação operacional da cobrança de um título. |
| `CollectionInteraction` | Contato registrado por canal e observação. |
| `PaymentPromise` | Promessa de pagamento com data e valor. |
| `PaymentAgreement` | Acordo negociado; possui uma ou mais parcelas. |
| `AgreementInstallment` | Parcela de acordo, data de vencimento e baixa. |
| `ImportBatch` / `ImportRejection` | Histórico de importação e linhas rejeitadas. |
| `ReportExecution` | Execução e arquivos gerados de relatórios. |
| `Notification` / `Recipient` | Histórico e destinatários de notificações. |
| `AuditLog` | Auditoria das operações relevantes. |

### Valores de um boleto

| Campo | Significado |
| --- | --- |
| `original_amount` | Valor original do documento. |
| `outstanding_amount` | Saldo em aberto informado pela origem. |
| `interest_amount` / `penalty_amount` | Juros e multa. |
| `balance_with_interest` | Saldo devido com juros (`SLD+JUR`); usado nos rankings de devedores. |
| `due_date` | Data real de vencimento, usada nos cálculos de atraso. |
| `source_overdue_days` | Dado de atraso recebido da origem, mantido para referência; não governa os cálculos. |

## 5. Autenticação e autorização

O sistema usa sessão Django. Todas as telas de negócio e APIs requerem usuário autenticado.

### Papéis

| Papel | Capacidades |
| --- | --- |
| Administrador | Acesso às operações, relatórios, dashboards e gestão de usuários. |
| Gestor | Acesso às operações, relatórios e dashboards; não gerencia usuários. |

Superusuários são tratados como Administradores. O salvamento de um usuário sincroniza `is_staff` com o papel Administrador.

### Gestão de usuários

A rota `/users/` é exclusiva para Administradores. Oferece:

- Busca e filtro por papel e situação.
- Cadastro de novos usuários, sempre ativos no momento da criação.
- Atribuição de Administrador ou Gestor.
- Edição de cadastro, papel e ativação/desativação.
- Redefinição de senha.
- Remoção quando não houver dependências históricas protegidas.
- Proteções contra desativar, remover ou remover o próprio papel administrativo.

As alterações são registradas em `AuditLog`.

## 6. Datas e cálculos de atraso

### Contrato de entrada

As fontes legadas e os formulários de negociação aceitam `MM/DD/AAAA` ou ISO (`AAAA-MM-DD`). A consulta SQL legada usa o estilo SQL Server `101`, que representa `MM/DD/AAAA`.

Uma data de origem `09/01/2026` é lida como 1º de setembro de 2026. Após armazenada em `DateField`, ela não carrega formato textual nem ambiguidade.

### Exibição

As telas detalhadas de boletos exibem emissão e vencimento como `DD/MM/AAAA`. Há telas, APIs e filtros antigos que ainda exibem ou solicitam `MM/DD/AAAA`; antes de padronizar globalmente a interface, preserve o contrato de importação.

### Regra de atraso

```text
dias de atraso = máximo(data de referência − data de vencimento, 0)
```

O campo `source_overdue_days` não é usado para decidir vencimento, faixa ou inadimplência.

Faixas usadas nos relatórios e indicadores:

| Dias em atraso | Faixa |
| --- | --- |
| 1 a 10 | Até 10 dias |
| 11 a 30 | De 11 a 30 dias |
| 31 a 90 | De 31 a 90 dias |
| 91 a 360 | De 91 a 360 dias |
| Acima de 360 | Acima de 360 dias |

## 7. Dashboards e rankings

### Indicadores

Os dashboards estaduais apresentam carteira, vencido acima de 10 dias e percentual de inadimplência. O cálculo de inadimplência usa a data de vencimento:

```text
inadimplência = total vencido / carteira total × 100
```

### Ranking dos 10 maiores grupos devedores

Para cada estado, o ranking considera apenas títulos que atendam a todos os critérios abaixo:

1. Vencimento há mais de 30 dias.
2. Situação financeira `open` ou `partially_paid`.
3. Saldo devido com juros (`balance_with_interest`) maior que zero.
4. Cliente sem promessa vigente e sem acordo ativo adimplente no escopo daquele dashboard.

Os valores elegíveis são somados por grupo econômico, ordenados do maior para o menor e limitados aos 10 primeiros. Empates são ordenados pelo nome do grupo.

Clicar em uma barra com grupo identificado abre a lista de boletos existente filtrada por esse grupo. Grupos sem identificação econômica não recebem link, pois não há filtro inequívoco para eles.

### Ranking dos 10 maiores devedores — CLIENTES GERAL

O segundo gráfico de cada dashboard estadual é fixo para o grupo econômico `CLIENTES GERAL` (comparação sem diferenciar maiúsculas/minúsculas e ignorando espaços externos). A elegibilidade é a mesma do ranking de grupos; os valores são somados por cliente, ordenados por saldo devido e limitados a 10 clientes.

Os rótulos longos são abreviados no gráfico para preservar o layout; o nome completo aparece no tooltip. Ao clicar na barra, o sistema abre a tela existente com os boletos do cliente.

### Promessas e acordos nos rankings

- Promessa pendente cuja data prometida ainda não passou: cliente fica fora do ranking.
- Acordo ativo sem parcela vencida em aberto: cliente fica fora do ranking.
- Promessa pendente com data já passada e sem pagamento: promessa é quebrada e o cliente volta ao ranking.
- Acordo ativo com parcela vencida e sem baixa: acordo é considerado descumprido e o cliente volta ao ranking.

A exclusão por compromisso é aplicada ao cliente inteiro dentro do estado visualizado, evitando que ele seja classificado como devedor enquanto cumpre uma negociação.

## 8. Cobrança e negociações

### Situações de cobrança

`CollectionStatus` aceita, entre outras, as situações: Pendente, Contactado, Promessa registrada, Em negociação, Pago, Não localizado, Promessa não cumprida e Acordo não cumprido.

### Promessas de pagamento

- A data pode ser de hoje até sete dias à frente.
- O valor pode corresponder ao boleto ou ao valor total selecionado.
- Ao registrar, a situação da cobrança passa a Promessa registrada.
- A tarefa diária identifica promessas pendentes cuja data já passou. Se o título não foi pago, a promessa é marcada como quebrada.

### Acordos

- Um acordo possui valor negociado, quantidade de parcelas, primeira data e periodicidade.
- As parcelas são criadas automaticamente, preservando o ajuste de centavos na última parcela.
- Uma parcela vencida sem `paid_at` caracteriza acordo não cumprido.

### Alertas de descumprimento

Às 06:00, a tarefa `verify_expired_promises` verifica promessas e parcelas de acordo. Ao identificar descumprimento, ela:

1. Atualiza o status de cobrança para promessa ou acordo não cumprido.
2. Mantém o título elegível aos rankings de devedores.
3. Envia e-mail ao operador do boleto; se não existir operador, usa o criador do compromisso como alternativa.
4. Evita duplicidade por chave de idempotência do compromisso e do operador.

O alerta depende de e-mail cadastrado no usuário responsável e de SMTP configurado. Sem e-mail, o evento é registrado no log técnico, mas não há destinatário para entrega.

## 9. Importação de dados

### Fontes

- **Excel padrão**: arquivo `.xlsx` com cabeçalhos obrigatórios descritos em [import-layout.md](import-layout.md).
- **Relatório legado**: arquivo Excel legado com cabeçalho em linha específica.
- **Banco SQL legado**: consulta somente leitura em SQL Server, normalizada pelo adaptador.

### Processo de importação

1. O arquivo/consulta é normalizado em `NormalizedReceivableRecord`.
2. Valores monetários e datas são convertidos e validados.
3. Estados, grupos econômicos, empresas e clientes são criados ou atualizados.
4. Boletos são inseridos/atualizados pela chave única empresa + documento + parcela.
5. Linhas inválidas são registradas em `ImportRejection` com número, motivo e conteúdo recebido.
6. `ImportBatch` registra contagens, situação e responsável.

## 10. Relatórios

O sistema produz Excel estadual consolidado, Excel por faixa de atraso e PDF executivo. Cada execução registra estado, tipo, data de referência, situação, arquivos, checksum, quantidade de linhas e mensagens de erro.

Comandos úteis:

```bash
python manage.py generate_collection_reports
python manage.py generate_collection_reports --state CE --pdf
python manage.py generate_collection_reports --date 09/08/2026
python manage.py run_collection_pipeline
python manage.py run_collection_pipeline --state BA
python manage.py run_collection_pipeline --skip-collection
```

## 11. Notificações

### E-mail

- Relatórios concluídos podem ser enviados a destinatários ativos por estado.
- Descumprimentos de promessas/acordos geram alerta específico ao operador responsável.
- Cada envio mantém tentativas, estado, erro e chave de idempotência.

### WhatsApp

A integração usa a API Meta Graph e webhook em `/api/webhooks/whatsapp/`. Credenciais e validação de assinatura são fornecidas exclusivamente por variáveis de ambiente.

## 12. API REST

Todas as APIs usam autenticação de sessão e exigem usuário autenticado.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| `GET, POST` | `/api/imports/` | Listar lotes e importar Excel. |
| `GET` | `/api/imports/<id>/` | Consultar lote de importação. |
| `GET` | `/api/receivables/` | Listar boletos; aceita `q`, `state`, `company`, `group`, `operator` e `status`. |
| `GET` | `/api/receivables/<id>/` | Detalhar boleto. |
| `GET` | `/api/collections/` | Listar cobranças. |
| `GET` | `/api/collections/<id>/` | Detalhar cobrança. |
| `PATCH/PUT` | `/api/collections/<id>/status/` | Atualizar situação de cobrança. |
| `POST` | `/api/collections/<id>/interactions/` | Registrar contato. |
| `POST` | `/api/collections/<id>/payment-promises/` | Criar promessa. |
| `POST` | `/api/collections/<id>/agreements/` | Criar acordo. |
| `GET` | `/api/reports/` | Listar relatórios. |
| `POST` | `/api/reports/generate/` | Gerar relatórios; Administrador ou Gestor. |
| `GET` | `/api/reports/<id>/` | Detalhar relatório. |
| `GET` | `/api/dashboards/summary/` | Indicadores do dashboard. |
| `GET` | `/api/dashboards/top-groups/` | Ranking de grupos pela regra de devedor. |
| `GET` | `/api/dashboards/top-customers/` | Ranking de CLIENTES GERAL. |

## 13. Rotas web principais

| Rota | Tela |
| --- | --- |
| `/` | Visão geral. |
| `/states/<UF>/` | Dashboard estadual. |
| `/receivables/` | Lista de boletos/clientes com filtros. |
| `/receivables/customers/<id>/` | Boletos e negociações de um cliente. |
| `/receivables/<id>/` | Detalhe de um boleto. |
| `/reports/` | Relatórios disponíveis. |
| `/users/` | Gestão de usuários; exclusiva para Administradores. |
| `/admin/` | Administração Django; acesso administrativo. |

## 14. Tarefas agendadas

| Horário | Tarefa | Função |
| --- | --- | --- |
| 06:00 | `verify_expired_promises` | Verifica promessas e acordos descumpridos. |
| 08:00 | `run_full_collection_pipeline` | Coleta dados, gera relatórios e envia notificações. |
| 14:00 | `run_supplementary_collection` | Executa coleta complementar. |
| 23:00 | `run_daily_backup` | Executa backup compatível com o banco configurado. |

Os horários seguem `America/Sao_Paulo`.

## 15. Execução local e Docker

### Ambiente Python local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Docker Compose

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose ps
```

O serviço `web` publica a porta `8000`. Banco, Redis, worker e beat se comunicam pela rede interna do Compose. Para evitar colisão com outro PostgreSQL do host, o banco do CRED-COBR não precisa expor a porta 5432 externamente.

## 16. Configuração por ambiente

| Variável | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta Django. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos. |
| `DATABASE_URL` | Conexão PostgreSQL; sem ela, usa SQLite local. |
| `REDIS_URL` | Broker/cache Redis. |
| `EMAIL_BACKEND`, `SMTP_*` | Entrega de e-mails. |
| `DEFAULT_FROM_EMAIL` | Remetente padrão. |
| `META_*` | Credenciais e parâmetros da integração WhatsApp. |
| `REPORTS_DIR` | Diretório de artefatos de relatório. |
| `BACKUPS_DIR` | Diretório de backups. |

Nunca versione o arquivo `.env` ou credenciais.

## 17. Segurança e operação

- Use HTTPS/TLS fora do desenvolvimento.
- Defina uma chave Django exclusiva em produção.
- Restrinja `DJANGO_ALLOWED_HOSTS` e origens CSRF.
- Mantenha SMTP, Meta e bancos em variáveis de ambiente/gerenciador de segredos.
- Revogue ou desative usuários que não precisem de acesso.
- Monitore `ImportBatch`, `ReportExecution`, `Notification` e logs de tarefa.
- Execute migrações antes de reiniciar serviços após mudanças de modelo.

## 18. Verificação

```bash
python manage.py check
pytest
```

Os testes cobrem regras de cálculo, importação, permissões, cobranças, relatórios, tarefas e gestão de usuários.

## 19. Referências complementares

- [README do projeto](../README.md)
- [Layout de importação](import-layout.md)
- [PRD](../PRD.md)
