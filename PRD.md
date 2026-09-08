# PRD — Automação de Relatórios e Gestão de Cobrança

<document_metadata>
  <title>Automação de Relatórios e Gestão de Cobrança</title>
  <document_type>Product Requirements Document</document_type>
  <version>1.0</version>
  <status>Planejado</status>
  <language>pt-BR</language>
  <timezone>America/Fortaleza</timezone>
  <primary_stack>Python 3.11+, Django 4.2 LTS, Django REST Framework, PostgreSQL</primary_stack>
  <deployment>Servidor Linux em rede local</deployment>
</document_metadata>

---

## 1. Prompt mestre para o agente de programação

<system_role>
Você é um arquiteto de software sênior e engenheiro full-stack especialista em Python, Django, Django REST Framework, PostgreSQL, processamento ETL, geração de relatórios, integrações empresariais, segurança, observabilidade e automação de tarefas.

Sua responsabilidade é implementar o sistema descrito neste PRD com código de produção, testável, seguro, modular e documentado.

Você DEVE obedecer integralmente às regras, restrições, requisitos e critérios de aceitação deste documento.
</system_role>

<execution_mode>
Trabalhe exclusivamente na tarefa explicitamente informada em <current_task>.

Antes de alterar qualquer arquivo, você DEVE:

1. Ler este PRD por completo.
2. Inspecionar a estrutura atual do projeto.
3. Identificar os arquivos estritamente necessários.
4. Verificar dependências e impactos.
5. Apresentar um plano curto de execução.
6. Implementar somente o escopo solicitado.
7. Executar testes e validações relacionados.
8. Informar exatamente o que foi alterado.

NÃO avance para outra sprint ou funcionalidade sem solicitação explícita.
</execution_mode>

<mandatory_rules>
- NÃO altere funcionalidades fora da tarefa atual.
- NÃO remova código existente sem justificativa técnica comprovada.
- NÃO modifique regras de negócio definidas neste PRD.
- NÃO invente campos, endpoints, credenciais, integrações ou requisitos.
- NÃO execute git commit, git push, merge, rebase ou alteração remota.
- NÃO altere configurações do Git ou GitHub.
- NÃO use credenciais reais no código, testes, exemplos ou documentação.
- NÃO exponha CPF, CNPJ, tokens, senhas, chaves ou dados financeiros em logs.
- NÃO use automação de navegador quando existir API, SQL ou exportação oficial.
- NÃO use o servidor de desenvolvimento do Django em produção.
- NÃO silencie exceções com blocos genéricos sem logging e tratamento.
- NÃO marque uma tarefa como concluída se testes, lint ou validações falharem.
- NÃO crie dependências desnecessárias.
- NÃO faça refatorações amplas sem solicitação explícita.
- NÃO implemente código fictício, pseudocódigo ou funções vazias como entrega final.
</mandatory_rules>

<engineering_standards>
Todo código produzido DEVE:

- Usar type hints.
- Seguir PEP 8.
- Separar regras de negócio, infraestrutura e apresentação.
- Aplicar princípios SOLID quando apropriado.
- Evitar duplicação de lógica.
- Usar transações nas operações críticas.
- Ser idempotente em importações, tarefas agendadas e notificações.
- Possuir tratamento explícito de erros.
- Produzir logs estruturados e rastreáveis.
- Validar entradas externas.
- Usar consultas parametrizadas ou ORM.
- Possuir testes unitários e, quando necessário, testes de integração.
- Usar variáveis de ambiente para configurações sensíveis.
- Manter compatibilidade com a arquitetura definida.
</engineering_standards>

<required_response_format>
Ao concluir cada tarefa, responda obrigatoriamente com:

1. **Resumo da implementação**
2. **Arquivos criados**
3. **Arquivos alterados**
4. **Regras de negócio implementadas**
5. **Testes executados**
6. **Resultado dos testes**
7. **Riscos ou pendências**
8. **Comandos para validação manual**
9. **Confirmação de que nenhuma alteração fora do escopo foi realizada**
</required_response_format>

<failure_policy>
Quando houver ambiguidade crítica, dependência ausente ou impossibilidade técnica:

- NÃO invente uma solução.
- Preserve o código existente.
- Registre a limitação.
- Utilize adaptadores, interfaces ou mocks apenas quando claramente identificados.
- Solicite decisão somente quando a ausência impedir a implementação correta.
</failure_policy>

<current_task>
Implemente apenas a sprint ou tarefa explicitamente solicitada pelo usuário.

TAREFA:
[INSERIR AQUI A SPRINT, HISTÓRIA OU ALTERAÇÃO]
</current_task>

---

## 2. Visão do produto

<product_vision>
Construir uma aplicação interna para automatizar a coleta, consolidação, análise, geração e distribuição de relatórios de cobrança de CE, BA e PE, incluindo o acompanhamento das ações dos gestores.

Em Pernambuco, os dados das empresas Nova e Multi devem permanecer identificáveis na base, mas devem ser consolidados nos relatórios e indicadores estaduais.
</product_vision>

<business_goals>
- Reduzir tarefas manuais de consolidação de dados.
- Padronizar relatórios de cobrança.
- Disponibilizar indicadores gerenciais atualizados.
- Automatizar envios por e-mail e WhatsApp.
- Registrar histórico das ações de cobrança.
- Aumentar rastreabilidade, segurança e confiabilidade.
</business_goals>

---

## 3. Escopo

<in_scope>
- Importação por banco de dados, API do BI Itecnove e Excel.
- Normalização e deduplicação dos registros.
- Consolidação por estado.
- Classificação dos títulos por dias de vencimento.
- Geração de relatórios Excel.
- Geração de dashboards executivos.
- Envio por e-mail institucional.
- Envio de resumos e notificações pela API oficial da Meta.
- Gestão de status de cobrança.
- Registro de previsões e acordos.
- Histórico e auditoria.
- Execução automática e manual.
- Hospedagem em servidor da rede local.
</in_scope>

<out_of_scope>
- Aplicativo móvel nativo.
- Substituição do ERP ou sistema financeiro principal.
- Alteração automática no banco legado.
- Cobrança automática enviada diretamente aos clientes finais na primeira versão.
- Integrações não descritas neste PRD.
- Inteligência artificial para tomar decisões financeiras.
- Automação por scraping sem aprovação explícita.
</out_of_scope>

---

## 4. Usuários e permissões

<user_roles>
  <role name="Administrador">
    Possui acesso total a todas as funcionalidades e a todos os estados. É o único perfil autorizado a cadastrar, alterar, ativar ou desativar usuários. Também gerencia fontes, destinatários, integrações, agendamentos e configurações.
  </role>

  <role name="Gestor">
    Possui acesso funcional completo a todos os estados, painéis, dashboards, boletos, relatórios, históricos, contatos, status, previsões, acordos e operações de cobrança. Não pode cadastrar, alterar, ativar, desativar ou administrar usuários.
  </role>
</user_roles>

<role_rules>
- O sistema deve possuir exatamente dois perfis de usuário: Administrador e Gestor.
- Somente o Administrador pode acessar a administração de usuários.
- O cadastro de usuário deve exigir um número de WhatsApp válido no formato internacional, com código do país e DDD.
- O Gestor possui todas as demais permissões funcionais do sistema.
- Ambos os perfis visualizam CE, BA e PE, incluindo a consolidação de Nova e Multi em Pernambuco.
- Auditoria permanece uma capacidade do sistema e uma trilha imutável, não um perfil de usuário.
</role_rules>

---

## 5. Requisitos funcionais

### RF-001 — Autenticação e autorização

<requirement id="RF-001" priority="must">
O sistema deve autenticar usuários individualmente e restringir a administração de usuários exclusivamente ao perfil Administrador. Administrador e Gestor acessam os dados funcionais de CE, BA e PE.
</requirement>

### RF-001.1 — Administração de usuários

<requirement id="RF-001.1" priority="must">
O sistema deve permitir cadastrar, alterar, ativar e desativar usuários somente ao Administrador. Novos usuários devem ser criados com um dos dois perfis válidos, Administrador ou Gestor, e possuir número de WhatsApp obrigatório no formato internacional, incluindo código do país e DDD. O Gestor não pode acessar telas, endpoints ou ações de administração de usuários.
</requirement>

### RF-002 — Cadastro de estados e empresas

<requirement id="RF-002" priority="must">
O sistema deve cadastrar CE, BA e PE, além das empresas associadas. Nova e Multi devem ser relacionadas a PE.
</requirement>

### RF-003 — Coleta via banco de dados

<requirement id="RF-003" priority="must">
O sistema deve coletar dados do banco legado usando credencial somente leitura e consultas parametrizadas.
</requirement>

### RF-004 — Coleta via BI Itecnove

<requirement id="RF-004" priority="must">
O sistema deve integrar-se preferencialmente por API oficial, consulta autorizada ou exportação estruturada do BI Itecnove.
</requirement>

### RF-005 — Importação de Excel

<requirement id="RF-005" priority="must">
O sistema deve importar arquivos .xlsx, validar colunas, tipos, duplicidades e registros inválidos.
</requirement>

### RF-006 — Normalização

<requirement id="RF-006" priority="must">
O sistema deve transformar todas as fontes em um modelo interno único.
</requirement>

### RF-007 — Deduplicação

<requirement id="RF-007" priority="must">
O sistema deve evitar duplicidade usando uma chave composta configurável, preferencialmente empresa, título e parcela.
</requirement>

### RF-008 — Classificação por vencimento

<requirement id="RF-008" priority="must">
O sistema deve calcular os dias vencidos com base na data corrente e classificar os títulos em:

- 1 a 10 dias;
- 11 a 30 dias;
- 31 a 90 dias;
- 91 a 360 dias;
- acima de 360 dias, para controle interno.
</requirement>

### RF-009 — Consolidação de Pernambuco

<requirement id="RF-009" priority="must">
Os dados de Nova e Multi devem ser preservados por empresa e consolidados para indicadores e relatórios de PE.
</requirement>

### RF-010 — Relatórios operacionais

<requirement id="RF-010" priority="must">
O sistema deve produzir 12 recortes operacionais, correspondentes a quatro faixas para cada um dos três estados.

A saída padrão deve ser:

- um arquivo Excel consolidado para CE com quatro abas;
- um arquivo Excel consolidado para BA com quatro abas;
- um arquivo Excel consolidado para PE com quatro abas, reunindo Nova e Multi;
- doze arquivos individuais obrigatórios, um para cada combinação de estado e faixa;
- filtros combináveis na página web de relatórios para faixa de vencimento, estado e data de referência;
- o filtro de faixa deve oferecer: Até 10 dias, De 11 a 30 dias, De 31 a 90 dias e De 91 a 360 dias;
- o resultado filtrado deve apresentar os relatórios de CE, BA e PE com download próprio;
- os filtros devem seguir os componentes, tokens, espaçamentos, estados de foco e responsividade do design system aprovado;
- a classificação deve usar a diferença entre a data de referência atual e a data de vencimento do boleto.
</requirement>

### RF-011 — Conteúdo do Excel

<requirement id="RF-011" priority="must">
Cada planilha deve apresentar:

- ID do título;
- parcela;
- ID do cliente;
- nome do cliente;
- grupo;
- empresa;
- estado;
- valor original;
- juros;
- multa;
- saldo em aberto;
- emissão;
- vencimento;
- dias vencidos;
- faixa;
- status financeiro;
- gestor responsável;
- status da cobrança;
- previsão de pagamento;
- última interação.
</requirement>

### RF-012 — Dashboard gerencial

<requirement id="RF-012" priority="must">
O sistema deve disponibilizar uma interface gráfica web completa, acessível por navegador na rede local, com dashboards por estado contendo:

- carteira total;
- total vencido;
- inadimplência;
- quantidade de títulos;
- clientes inadimplentes;
- dez maiores grupos devedores;
- dez maiores clientes do grupo CLIENTES GERAL;
- promessas de pagamento vencidas.
</requirement>

### RF-012.1 — Página inicial

<requirement id="RF-012.1" priority="must">
A página inicial deve apresentar um resumo executivo com:

- métricas gerais;
- indicadores por estado;
- total da carteira;
- total vencido acima de 10 dias;
- percentual de inadimplência;
- quantidade de boletos;
- quantidade de clientes inadimplentes;
- promessas de pagamento vencidas;
- data e hora da última atualização;
- alertas de falha em importações ou distribuições.
- caixas independentes para vencido total e para as faixas de 1–10, 11–30, 31–90, 91–360 e acima de 360 dias;
- caixas independentes de inadimplência para CE, BA e PE;
- promessas vencidas e quantidade de acordos feitos por usuários gestores.
</requirement>

### RF-012.2 — Visualização de relatórios por estado

<requirement id="RF-012.2" priority="must">
A interface deve permitir selecionar CE, BA ou PE e visualizar:

- resumo estadual;
- relatórios disponíveis organizados por filtros combináveis de faixa, estado e data de referência;
- os downloads estaduais correspondentes aos filtros selecionados;
- data de geração;
- situação da geração;
- opção de download;
- filtros por período;
- filtros por faixa de vencimento;
- filtros por empresa, quando aplicável;
- visualização consolidada de PE, mantendo Nova e Multi identificáveis.
</requirement>

### RF-012.3 — Tabelas de boletos vencidos

<requirement id="RF-012.3" priority="must">
O sistema deve exibir tabelas paginadas e pesquisáveis de boletos vencidos, contendo no mínimo:

- identificação do boleto;
- cliente;
- grupo;
- empresa;
- estado;
- valor em aberto;
- vencimento;
- dias vencidos;
- faixa;
- gestor responsável;
- status da cobrança;
- previsão de pagamento;
- última interação.

As tabelas devem oferecer ordenação, paginação, filtros e acesso ao detalhe do boleto.
</requirement>

### RF-012.4 — Atualização de status pela interface

<requirement id="RF-012.4" priority="must">
Usuários autorizados devem conseguir atualizar pela interface gráfica:

- status da cobrança;
- observações;
- previsão de pagamento;
- valor previsto;
- próxima ação;
- detalhes de acordo;
- responsável pela atualização.

Toda alteração deve gerar histórico imutável e registro de auditoria.
</requirement>

### RF-012.5 — Formulários de pesquisa

<requirement id="RF-012.5" priority="must">
A interface deve possuir formulários de pesquisa e filtros combináveis por:

- cliente;
- CPF ou CNPJ, com exibição mascarada;
- ID do boleto;
- grupo;
- estado;
- empresa;
- gestor responsável;
- status;
- período de vencimento;
- faixa de atraso;
- previsão de pagamento.
</requirement>

### RF-012.6 — Gráficos

<requirement id="RF-012.6" priority="must">
A interface deve apresentar gráficos com Chart.js, ou biblioteca equivalente aprovada, para:

- inadimplência por estado;
- distribuição dos valores por faixa de vencimento;
- dez maiores grupos devedores;
- dez maiores clientes do grupo CLIENTES GERAL;
- evolução da inadimplência;
- promessas de pagamento por situação.

Os gráficos devem utilizar dados fornecidos pelo backend, sem duplicar regras de negócio no navegador.

Para cada estado (CE, BA e PE, com Nova e Multi consolidadas em PE), o dashboard deve exibir os dez maiores grupos e os dez maiores clientes do grupo CLIENTES GERAL em gráficos de barras separados, empilhados verticalmente. O comparativo de inadimplência deve ser um gráfico comparativo entre estados. O percentual considera somente títulos vencidos há mais de 10 dias: vencido acima de 10 dias dividido pela carteira total (a vencer + vencida), multiplicado por 100.
</requirement>

### RF-012.7 — Responsividade

<requirement id="RF-012.7" priority="must">
A interface deve funcionar em desktop, tablet e dispositivos móveis.

Em telas menores:

- o menu deve ser recolhível;
- tabelas devem possuir rolagem horizontal ou visualização adaptada;
- cartões devem reorganizar-se verticalmente;
- filtros devem permanecer acessíveis;
- ações principais devem ser utilizáveis por toque;
- textos e controles não podem se sobrepor.
</requirement>

### RF-012.8 — Estados da interface

<requirement id="RF-012.8" priority="must">
Todas as páginas devem tratar explicitamente:

- carregamento;
- ausência de dados;
- erro;
- acesso negado;
- sucesso de operação;
- confirmação antes de ações sensíveis;
- falha de comunicação com o backend.
</requirement>

### RF-012.9 — Acessibilidade e usabilidade

<requirement id="RF-012.9" priority="should">
A interface deve:

- utilizar HTML semântico;
- permitir navegação por teclado;
- possuir contraste legível;
- exibir rótulos nos campos;
- apresentar mensagens de validação claras;
- preservar foco em modais e formulários;
- evitar depender exclusivamente de cores para transmitir status.
</requirement>

### RF-013 — Cálculo de inadimplência

<requirement id="RF-013" priority="must">
A inadimplência deve ser calculada por:

valor vencido acima de 10 dias / carteira total × 100

A carteira total deve considerar valores a vencer e vencidos, conforme regra validada pela empresa.
</requirement>

### RF-014 — Envio por e-mail

<requirement id="RF-014" priority="must">
O sistema deve enviar relatórios pelo SMTP institucional, com destinatários configuráveis por estado e perfil.
</requirement>

### RF-015 — Envio pelo WhatsApp

<requirement id="RF-015" priority="must">
O sistema deve enviar resumos e alertas pela WhatsApp Business Platform, usando templates aprovados quando exigido.
</requirement>

### RF-016 — Webhook do WhatsApp

<requirement id="RF-016" priority="should">
O sistema deve receber eventos de entrega, leitura e respostas por endpoint HTTPS autenticado e validado.
</requirement>

### RF-017 — Status de cobrança

<requirement id="RF-017" priority="must">
O gestor deve registrar o status atual da cobrança, observações, canal, responsável, data e próxima ação.
</requirement>

### RF-018 — Previsão de pagamento

<requirement id="RF-018" priority="must">
O sistema deve permitir registrar data, valor e situação da promessa de pagamento.
</requirement>

### RF-019 — Acordos

<requirement id="RF-019" priority="must">
O sistema deve registrar valor negociado, quantidade de parcelas, periodicidade, vencimentos e situação de cada parcela.
</requirement>

### RF-020 — Histórico imutável

<requirement id="RF-020" priority="must">
Cada alteração de cobrança deve gerar um histórico com usuário, data, valor anterior, valor novo, origem e motivo.
</requirement>

### RF-021 — Agendamento

<requirement id="RF-021" priority="must">
O sistema deve executar:

- processo completo diariamente às 08:00;
- coleta complementar às 14:00;
- verificação periódica de promessas vencidas;
- backup diário.
</requirement>

### RF-022 — Execução manual

<requirement id="RF-022" priority="must">
O sistema deve oferecer comando administrativo para importar, processar, gerar e enviar relatórios manualmente.
</requirement>

### RF-023 — Idempotência

<requirement id="RF-023" priority="must">
A repetição de uma tarefa não deve duplicar registros, relatórios, históricos ou notificações.
</requirement>

### RF-024 — Logs e auditoria

<requirement id="RF-024" priority="must">
O sistema deve registrar execução, duração, origem, volume processado, falhas, tentativas e responsável.
</requirement>

---

## 6. Requisitos não funcionais

<non_functional_requirements>
  <performance>
    - Processar pelo menos 5.000 títulos em até 30 segundos em ambiente homologado.
    - Gerar os relatórios estaduais em até 2 minutos.
    - Responder endpoints comuns em até 500 ms no percentil 95, desconsiderando integrações externas.
  </performance>

  <security>
    - Credenciais somente em variáveis de ambiente ou cofre de segredos.
    - HTTPS obrigatório para autenticação e webhook.
    - Proteção contra CSRF, XSS, SQL injection e upload malicioso.
    - Princípio do menor privilégio.
    - Mascaramento de dados sensíveis.
    - Auditoria de operações críticas.
  </security>

  <reliability>
    - Retry exponencial para integrações externas.
    - Timeout explícito em chamadas HTTP.
    - Transações nas operações críticas.
    - Sem perda silenciosa de registros.
    - Prevenção de tarefas concorrentes duplicadas.
  </reliability>

  <maintainability>
    - Código modular.
    - Type hints.
    - Testes automatizados.
    - Documentação de instalação e operação.
    - Adaptadores independentes para fontes e canais.
  </maintainability>

  <deployment>
    - Aplicação executada em Linux.
    - Docker Compose recomendado.
    - Nginx como proxy reverso.
    - Gunicorn como servidor WSGI.
    - PostgreSQL como banco principal.
    - Redis e Celery para filas e agendamentos.
  </deployment>
</non_functional_requirements>

---

## 7. Stack tecnológica

<technology_stack>
  <backend>Python 3.11+ e Django 4.2 LTS</backend>
  <api>Django REST Framework</api>
  <frontend>Django Templates, HTML5, CSS3 e JavaScript modular</frontend>
  <ui_framework>Bootstrap 5 ou CSS próprio baseado em design system aprovado</ui_framework>
  <charts>Chart.js</charts>
  <database>PostgreSQL</database>
  <queue>Celery</queue>
  <broker>Redis</broker>
  <scheduler>Celery Beat</scheduler>
  <excel>Pandas e OpenPyXL</excel>
  <pdf>ReportLab ou WeasyPrint, mediante validação técnica</pdf>
  <http_client>HTTPX ou Requests com timeout e retry</http_client>
  <email>SMTP institucional</email>
  <whatsapp>WhatsApp Business Platform Cloud API</whatsapp>
  <server>Gunicorn e Nginx</server>
  <containers>Docker Compose</containers>
  <tests>Pytest, pytest-django e factories</tests>
</technology_stack>

---

## 8. Arquitetura esperada

```text
projeto_cobranca/
├── apps/
│   ├── accounts/
│   ├── companies/
│   ├── customers/
│   ├── receivables/
│   ├── collections/
│   ├── imports/
│   │   ├── adapters/
│   │   ├── services/
│   │   └── tasks.py
│   ├── reports/
│   │   ├── generators/
│   │   ├── services/
│   │   └── tasks.py
│   ├── dashboards/
│   ├── notifications/
│   │   ├── email/
│   │   ├── whatsapp/
│   │   └── tasks.py
│   └── audit/
├── templates/
│   ├── base.html
│   ├── dashboard/
│   ├── reports/
│   ├── receivables/
│   ├── collections/
│   └── components/
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── vendor/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── tests/
│   ├── ui/
│   ├── api/
│   └── services/
├── scripts/
├── deploy/
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 9. Modelo de domínio mínimo

<domain_models>
  <model name="Company">
    Empresa vinculada a um estado.
  </model>

  <model name="Customer">
    Cliente com identificador, documento, grupo e dados de contato.
  </model>

  <model name="EconomicGroup">
    Grupo econômico usado nas consolidações.
  </model>

  <model name="Receivable">
    Título ou boleto com valores, vencimento, empresa, cliente e situação.
  </model>

  <model name="ImportBatch">
    Lote de importação com origem, status, totais, erros e duração.
  </model>

  <model name="CollectionStatus">
    Situação atual da cobrança.
  </model>

  <model name="CollectionInteraction">
    Registro imutável de contato ou alteração.
  </model>

  <model name="PaymentPromise">
    Previsão de pagamento.
  </model>

  <model name="PaymentAgreement">
    Acordo negociado.
  </model>

  <model name="AgreementInstallment">
    Parcela de um acordo.
  </model>

  <model name="ReportExecution">
    Histórico de geração de relatório.
  </model>

  <model name="Notification">
    Histórico de e-mail ou WhatsApp.
  </model>

  <model name="AuditLog">
    Trilha de auditoria.
  </model>
</domain_models>

---

## 10. Endpoints mínimos

```text
POST   /api/imports/
GET    /api/imports/
GET    /api/imports/{id}/

GET    /api/receivables/
GET    /api/receivables/{id}/

GET    /api/collections/
GET    /api/collections/{id}/
PATCH  /api/collections/{id}/status/
POST   /api/collections/{id}/interactions/
POST   /api/collections/{id}/payment-promises/
POST   /api/collections/{id}/agreements/

POST   /api/reports/generate/
GET    /api/reports/
GET    /api/reports/{id}/download/

GET    /api/dashboards/summary/
GET    /api/dashboards/top-groups/
GET    /api/dashboards/top-customers/

POST   /api/webhooks/whatsapp/
GET    /api/webhooks/whatsapp/
```

DELETE físico de históricos, cobranças e registros financeiros não deve ser disponibilizado por padrão.

---

# 11. Plano de implementação por sprints

## Sprint 0 — Descoberta e validação técnica

<sprint id="SPRINT-0" objective="Eliminar incertezas antes da implementação">
  <tasks>
    - Mapear banco legado e campos disponíveis.
    - Validar acesso ao BI Itecnove.
    - Definir layout oficial do Excel.
    - Confirmar fórmula da carteira total.
    - Definir chave de deduplicação.
    - Definir destinatários e permissões.
    - Validar SMTP institucional.
    - Validar conta e número da Meta.
    - Produzir dicionário de dados.
  </tasks>

  <acceptance_criteria>
    - Fontes documentadas.
    - Campos obrigatórios identificados.
    - Regras de negócio aprovadas.
    - Credenciais de homologação disponíveis.
    - Layout de relatórios aprovado.
  </acceptance_criteria>
</sprint>

## Sprint 1 — Fundação do projeto

<sprint id="SPRINT-1" objective="Criar a base segura e executável">
  <tasks>
     - [X] Criar projeto Django.
     - [X] Configurar settings por ambiente.
     - [X] Configurar PostgreSQL.
     - [X] Configurar Docker Compose.
     - [X] Criar autenticação com os perfis Administrador e Gestor.
     - [X] Configurar logging.
     - [X] Configurar Pytest.
     - [X] Criar CI local ou pipeline de validação.
     - [X] Criar README e .env.example.
  </tasks>

  <acceptance_criteria>
    - Aplicação sobe em ambiente local.
    - Migrações executam sem erro.
    - Usuário administrador pode autenticar e cadastrar novos usuários.
    - Testes básicos passam.
    - Nenhuma credencial está no repositório.
  </acceptance_criteria>
</sprint>

## Sprint 2 — Modelo de domínio e auditoria

<sprint id="SPRINT-2" objective="Persistir entidades e histórico">
  <tasks>
     - [X] Implementar empresas, estados, clientes e grupos.
     - [X] Implementar títulos financeiros.
     - [X] Implementar lotes de importação.
     - [X] Implementar status e interações.
     - [X] Implementar auditoria.
     - [X] Criar índices e constraints.
     - [X] Criar factories e testes de modelo.
  </tasks>

  <acceptance_criteria>
    - Modelos representam o domínio mínimo.
    - Restrições impedem duplicidades críticas.
    - Alterações relevantes geram auditoria.
    - Testes de modelos passam.
  </acceptance_criteria>
</sprint>

## Sprint 3 — Importação Excel

<sprint id="SPRINT-3" objective="Entregar a primeira fonte funcional">
  <tasks>
     - [X] Criar upload seguro.
     - [X] Validar extensão, tamanho e cabeçalhos.
     - [X] Mapear colunas para o modelo interno.
     - [X] Normalizar datas, moedas e identificadores.
     - [X] Deduplicar registros.
     - [X] Gerar relatório de rejeições.
     - [X] Arquivar o arquivo processado.
     - [X] Implementar testes com arquivos válidos e inválidos.
  </tasks>

  <acceptance_criteria>
    - Arquivo válido é importado.
    - Arquivo inválido não altera dados.
    - Duplicidades são tratadas de forma idempotente.
    - Erros por linha são rastreáveis.
  </acceptance_criteria>
</sprint>

## Sprint 4 — Banco legado e BI Itecnove

<sprint id="SPRINT-4" objective="Completar os conectores de origem">
  <tasks>
     - [X] Criar interface comum de importadores.
     - [X] Implementar adaptador SQL somente leitura.
     - [X] Implementar adaptador Itecnove.
     - [X] Configurar timeout e retry.
     - [X] Criar mocks e testes de integração.
     - [X] Registrar métricas de cada coleta.
  </tasks>

  <acceptance_criteria>
    - As três fontes produzem o mesmo modelo interno.
    - Falha em uma fonte não corrompe dados existentes.
    - Execuções repetidas não duplicam títulos.
    - Segredos não aparecem em logs.
  </acceptance_criteria>
</sprint>

## Sprint 5 — Motor de processamento

<sprint id="SPRINT-5" objective="Implementar todas as regras financeiras do relatório">
  <tasks>
     - [X] Calcular dias vencidos.
     - [X] Classificar faixas.
     - [X] Consolidar Nova e Multi em PE.
     - [X] Calcular carteira total.
     - [X] Calcular inadimplência.
     - [X] Calcular top 10 grupos.
     - [X] Calcular top 10 CLIENTES GERAL.
     - [X] Criar testes de borda para 10, 11, 30, 31, 90, 91, 360 e 361 dias.
  </tasks>

  <acceptance_criteria>
    - Todos os limites de faixa são testados.
    - PE é consolidado sem perder identificação da empresa.
    - Indicadores batem com massa de dados homologada.
    - Cálculos usam Decimal.
  </acceptance_criteria>
</sprint>

## Sprint 6 — Relatórios Excel e PDF

<sprint id="SPRINT-6" objective="Gerar os artefatos operacionais e executivos">
  <tasks>
     - [X] Gerar Excel por estado.
     - [X] Criar quatro abas de vencimento.
     - [X] Criar aba de resumo.
     - [X] Aplicar filtros, totais e formatação.
     - [X] Gerar dashboard executivo em PDF.
     - [X] Registrar execução e checksum dos arquivos.
     - [X] Criar testes de conteúdo dos arquivos.
  </tasks>

  <acceptance_criteria>
    - CE, BA e PE geram arquivos válidos.
    - As 12 faixas estaduais estão presentes.
    - Totais dos arquivos conferem com o banco.
    - Arquivos possuem data e hora da geração.
  </acceptance_criteria>
</sprint>

## Sprint 7 — Interface gráfica e dashboard HTML

<sprint id="SPRINT-7" objective="Disponibilizar uma interface web completa, responsiva e segura">
  <tasks>
     - [X] Criar layout base com cabeçalho, menu lateral, área principal e rodapé.
     - [X] Criar design system com tipografia, espaçamentos, botões, cores, estados e componentes.
     - [X] Criar página inicial com métricas resumidas.
     - [X] Criar navegação por CE, BA e PE.
     - [X] Criar tela de relatórios por estado.
     - [X] Criar tabelas paginadas de boletos vencidos.
     - [X] Implementar pesquisa e filtros combináveis.
     - [X] Criar página de detalhe do boleto.
     - [X] Criar formulários para atualizar status, previsões e acordos.
     - [X] Criar gráficos com Chart.js.
     - [X] Criar componentes reutilizáveis de cartões, tabelas, filtros, modais e alertas.
     - [X] Implementar estados de carregamento, vazio, erro, sucesso e acesso negado.
     - [X] Implementar responsividade para mobile, tablet e desktop.
     - [X] Aplicar permissões de interface conforme perfil e estado.
     - [X] Garantir que cálculos sejam realizados no backend.
     - [X] Criar testes de views, templates, permissões, formulários e navegação.
  </tasks>

  <pages>
    - Login.
    - Página inicial.
    - Dashboard geral.
    - Dashboard por estado.
    - Lista de boletos.
    - Detalhe do boleto.
    - Atualização de cobrança.
    - Lista de relatórios.
    - Detalhe e download do relatório.
    - Promessas de pagamento.
    - Acordos.
    - Histórico de interações.
    - Administração de destinatários, quando autorizado.
  </pages>

  <ui_requirements>
    - HTML5 semântico.
    - CSS responsivo.
    - JavaScript modular.
    - Chart.js para gráficos.
    - Navegação utilizável por teclado.
    - Tabelas adaptadas a telas menores.
    - Feedback visual após operações.
    - Confirmação para ações sensíveis.
    - Mensagens de validação próximas aos campos.
    - Nenhuma regra financeira duplicada no frontend.
  </ui_requirements>

  <acceptance_criteria>
    - A página inicial exibe métricas resumidas e última atualização.
    - Usuários navegam pelos relatórios de CE, BA e PE.
    - Tabelas permitem pesquisar, filtrar, ordenar e paginar boletos.
    - Gestores atualizam status pela interface.
    - Atualizações geram histórico e auditoria.
    - Gráficos exibem dados coerentes com os relatórios.
    - Gestores visualizam CE, BA e PE.
    - Gestores não acessam a administração de usuários.
    - Interface funciona em larguras móveis e desktop.
    - Formulários exibem erros claros e preservam dados válidos.
    - Páginas possuem estados de carregamento, vazio e erro.
    - Testes de views, templates, formulários e permissões passam.
  </acceptance_criteria>
</sprint>

## Sprint 8 — Gestão de cobrança

<sprint id="SPRINT-8" objective="Registrar o trabalho dos gestores">
  <tasks>
     - [X] Implementar status de cobrança.
     - [X] Implementar interações.
     - [X] Implementar previsões.
     - [X] Implementar acordos e parcelas.
     - [X] Destacar promessas vencidas.
     - [X] Criar APIs e telas.
     - [X] Criar testes de permissão e transição.
  </tasks>

  <acceptance_criteria>
    - Gestor registra acompanhamento.
    - Histórico anterior não pode ser alterado.
    - Promessas vencidas são identificadas.
    - Acordos geram parcelas corretamente.
  </acceptance_criteria>
</sprint>

## Sprint 9 — E-mail institucional

<sprint id="SPRINT-9" objective="Automatizar a distribuição por e-mail">
  <tasks>
     - [X] Configurar SMTP.
     - [X] Criar destinatários por estado.
     - [X] Criar template HTML.
     - [X] Anexar Excel e PDF.
     - [X] Registrar envio, falha e tentativa.
     - [X] Implementar retry seguro.
  </tasks>

  <acceptance_criteria>
    - Relatórios chegam aos destinatários corretos.
    - Falhas ficam visíveis no painel e logs.
    - Reprocessamento não gera envio duplicado sem autorização.
  </acceptance_criteria>
</sprint>

## Sprint 10 — WhatsApp oficial

<sprint id="SPRINT-10" objective="Enviar alertas e atualizações pela Meta">
  <tasks>
     - [X] Integrar Cloud API.
     - [X] Configurar templates.
     - [X] Enviar resumos por estado.
     - [X] Registrar IDs e status.
     - [X] Implementar webhook HTTPS.
     - [X] Validar assinatura e token.
     - [X] Processar confirmação de entrega e leitura.
  </tasks>

  <acceptance_criteria>
    - Templates aprovados são enviados.
    - Eventos recebidos são autenticados.
    - Mensagens são associadas ao destinatário correto.
    - Tokens não aparecem em logs.
  </acceptance_criteria>
</sprint>

## Sprint 11 — Agendamento e CLI

<sprint id="SPRINT-11" objective="Operar sem intervenção manual">
  <tasks>
    - Configurar Celery e Redis.
    - Configurar Celery Beat.
    - Agendar processo das 08:00.
    - Agendar coleta das 14:00.
    - Criar locks de execução.
    - Criar management commands.
    - Criar alertas de falha.
  </tasks>

  <acceptance_criteria>
    - Apenas uma instância de cada tarefa executa.
    - Falhas são retomáveis.
    - Execução manual usa a mesma regra da execução automática.
    - Histórico registra cada etapa.
  </acceptance_criteria>
</sprint>

## Sprint 12 — Segurança, backup e implantação

<sprint id="SPRINT-12" objective="Colocar a aplicação em produção local">
  <tasks>
    - Configurar Gunicorn.
    - Configurar Nginx.
    - Configurar HTTPS interno.
    - Restringir portas e IPs.
    - Configurar backup automático.
    - Testar restauração.
    - Configurar rotação de logs.
    - Executar check de deploy.
    - Criar manual operacional.
  </tasks>

  <acceptance_criteria>
    - Sistema acessível apenas pela rede autorizada.
    - Backup é criado e restaurado com sucesso.
    - DEBUG está desabilitado.
    - Serviços reiniciam automaticamente.
    - Checklist de produção está aprovado.
  </acceptance_criteria>
</sprint>

---

## 12. Estratégia de testes

<test_strategy>
- Testes unitários para regras de faixa, indicadores e consolidação.
- Testes de modelo para constraints e transações.
- Testes de API para autenticação e permissões.
- Testes de views, templates e formulários.
- Testes responsivos e de navegação dos fluxos críticos.
- Testes de autorização das ações exibidas na interface.
- Testes de integração para banco, BI, SMTP e Meta usando mocks.
- Testes de geração de Excel e PDF.
- Testes de idempotência.
- Testes de concorrência nas tarefas.
- Testes de segurança de upload e entrada.
- Testes de recuperação de backup.
</test_strategy>

<minimum_quality_gate>
- Todos os testes relacionados à tarefa devem passar.
- Nenhuma migration pendente.
- Nenhuma credencial no código.
- Nenhum erro crítico de lint ou type checking.
- Cobertura mínima de 80% nos services de regra de negócio.
</minimum_quality_gate>

---

## 13. Definition of Ready

Uma história só pode ser iniciada quando:

- Possuir objetivo claro.
- Possuir regra de negócio definida.
- Possuir critérios de aceitação.
- Possuir dependências identificadas.
- Possuir dados de teste ou contrato de integração.
- Não depender de uma decisão empresarial desconhecida.

---

## 14. Definition of Done

Uma tarefa só pode ser concluída quando:

- Código implementado.
- Testes criados e aprovados.
- Migrações revisadas.
- Logs e erros tratados.
- Documentação atualizada.
- Segurança validada.
- Critérios de aceitação atendidos.
- Nenhuma alteração fora do escopo realizada.
- Resultado demonstrável em ambiente local.
- Pendências explicitamente registradas.

---

## 15. Comandos esperados

```bash
# Ambiente
docker compose up -d --build

# Migrações
python manage.py migrate

# Testes
pytest

# Validação Django
python manage.py check
python manage.py check --deploy

# Processo manual
python manage.py run_collection_pipeline --state CE --send

# Gerar sem enviar
python manage.py generate_collection_reports --date 2026-08-03

# Worker
celery -A config worker -l INFO

# Scheduler
celery -A config beat -l INFO
```

---

## 16. Variáveis de ambiente

```dotenv
DJANGO_SECRET_KEY=
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=

DATABASE_URL=
REDIS_URL=

LEGACY_DATABASE_URL=
ITECNOVE_BASE_URL=
ITECNOVE_TOKEN=

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=true
DEFAULT_FROM_EMAIL=

META_GRAPH_API_VERSION=
META_WHATSAPP_TOKEN=
META_PHONE_NUMBER_ID=
META_BUSINESS_ACCOUNT_ID=
META_WEBHOOK_VERIFY_TOKEN=
META_APP_SECRET=

REPORTS_DIR=
IMPORTS_DIR=
BACKUPS_DIR=
```

---

## 17. Critérios globais de aceitação

<global_acceptance_criteria>
- As três fontes podem ser processadas por adaptadores independentes.
- Os dados são normalizados e deduplicados.
- As quatro faixas são calculadas corretamente.
- Os 12 recortes estaduais são gerados.
- Nova e Multi são consolidadas em PE.
- Os dashboards apresentam os rankings exigidos.
- A interface gráfica permite visualizar relatórios e boletos por estado.
- A interface permite pesquisar, filtrar e paginar títulos.
- Usuários autorizados atualizam status de cobrança pela interface.
- Os gráficos são responsivos e utilizam dados calculados no backend.
- A interface funciona em mobile e desktop.
- A inadimplência exclui a faixa de até 10 dias.
- E-mails e WhatsApp são enviados aos destinatários configurados.
- Gestores registram status, previsões e acordos.
- Todas as alterações relevantes possuem auditoria.
- O sistema executa automaticamente às 08:00 e 14:00.
- Nenhuma credencial está hardcoded.
- O ambiente de produção roda na rede local com backup.
</global_acceptance_criteria>

---

## 18. Instrução final para execução pelo agente

<final_instruction>
Leia este documento integralmente.

Implemente somente o conteúdo informado em <current_task>.

Não altere arquivos, regras ou funcionalidades fora do escopo solicitado.

Antes de codificar, apresente o plano e os arquivos que serão afetados.

Depois de codificar, execute os testes relacionados e entregue o relatório no formato obrigatório.

Caso uma regra esteja ausente, não invente. Registre a lacuna e preserve a arquitetura.

TAREFA ATUAL:

[SUBSTITUIR PELA SPRINT OU ALTERAÇÃO DESEJADA]
</final_instruction>
