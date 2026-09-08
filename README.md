# CRED-COBR

Sistema de gestão de cobrança construído em Django. Centraliza importações, carteira de recebíveis, acompanhamento de negociações, geração de relatórios por estado e notificações por e-mail.

## Principais recursos

- Gestão de clientes, empresas, títulos a receber e atividades de cobrança;
- Importação e normalização de dados de sistemas legados;
- Painel com indicadores operacionais e filtros por estado;
- Relatórios de inadimplência em Excel e PDF para CE, BA e PE;
- Registro auditável de execuções, notificações e tentativas de envio;
- API autenticada, área administrativa e controle de permissões;
- Processamento assíncrono com Celery e agendamento com Celery Beat.

## Tecnologias

- Python 3.12+ e Django 5;
- Django REST Framework;
- PostgreSQL ou SQLite para desenvolvimento local;
- Redis, Celery e Celery Beat;
- Pandas, OpenPyXL e ReportLab;
- Docker e Docker Compose (opcional).

## Estrutura do projeto

```text
apps/          Domínios da aplicação (importações, cobrança, relatórios e notificações)
core/          Configuração Django, Celery, URLs e tarefas de infraestrutura
shared/        Utilitários e modelos compartilhados
templates/     Interfaces HTML
static/        Estilos e scripts
docs/          Documentação complementar
```

## Pré-requisitos

- Python 3.12 ou superior;
- `pip` e ambiente virtual;
- Redis, para filas assíncronas fora do modo local;
- PostgreSQL, se não for usar SQLite local;
- Docker Desktop, opcionalmente, para executar os serviços em contêineres.

## Configuração local

1. Crie e ative o ambiente virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   No Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Crie o arquivo `.env` na raiz do projeto. Ele é local e não deve ser versionado. Para desenvolvimento mínimo, defina:

   ```env
   DJANGO_SECRET_KEY=defina-uma-chave-local-segura
   DJANGO_DEBUG=true
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   ```

   As configurações de banco, Redis, e-mail e integrações devem ser fornecidas exclusivamente por variáveis de ambiente. Nunca registre senhas, tokens, endereços internos, arquivos de importação ou relatórios no Git.

4. Aplique as migrações e crie um usuário administrador:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Inicie a aplicação:

   ```bash
   python manage.py runserver
   ```

   Acesse `http://127.0.0.1:8000/` e a administração em `http://127.0.0.1:8000/admin/`.

## Serviços assíncronos

Com Redis configurado, inicie os processos em terminais separados:

```bash
celery -A core worker -l INFO
celery -A core beat -l INFO
```

Na ausência de Redis, o ambiente de desenvolvimento pode executar tarefas de forma síncrona, conforme as configurações locais.

## Docker

Com um `.env` local configurado, execute:

```bash
docker compose up --build
```

O Compose disponibiliza aplicação web, PostgreSQL, Redis, worker Celery e agendador. Os volumes de relatórios e importações são persistidos fora do código versionado.

## Operação

Gere relatórios para todos os estados ou para um estado específico:

```bash
python manage.py generate_collection_reports
python manage.py generate_collection_reports --state CE --pdf
python manage.py generate_collection_reports --date 09/08/2026
```

Execute o pipeline de coleta, processamento e relatórios:

```bash
python manage.py run_collection_pipeline
python manage.py run_collection_pipeline --state BA
python manage.py run_collection_pipeline --skip-collection
```

Os arquivos produzidos ficam no diretório local de relatórios. Eles são intencionalmente ignorados pelo Git.

## Testes e verificações

```bash
pytest
python manage.py check
```

## Segurança e dados

O repositório ignora arquivos de ambiente, bancos locais, mídia, relatórios gerados, importações, planilhas de exemplo e backups. Antes de implantar em produção:

- use uma chave Django exclusiva e segura;
- configure `DJANGO_ALLOWED_HOSTS` e origens CSRF confiáveis;
- utilize TLS/HTTPS;
- mantenha credenciais em um gerenciador de segredos ou variáveis do ambiente de execução;
- configure autenticação SMTP e DNS do domínio remetente para notificações por e-mail;
- limite o acesso aos arquivos de importação e relatórios gerados.

## Documentação adicional

Consulte [docs/import-layout.md](docs/import-layout.md) para o formato esperado das importações.
