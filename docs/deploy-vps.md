# Implantação em VPS própria

Este procedimento parte de uma instalação nova. Use Docker Engine e Docker Compose v2.
O arquivo `compose.production.yml` é independente do Compose de desenvolvimento.
Sempre informe `-f compose.production.yml`; assim o `docker-compose.override.yml`
local não é aplicado.

## 1. Preparar a VPS

- Instale Docker Engine e o plugin Docker Compose.
- Configure DNS e um proxy reverso HTTPS na VPS. A aplicação escuta somente em
  `127.0.0.1:8000` no host; PostgreSQL e Redis não publicam portas.
- Libere no firewall apenas as portas necessárias para SSH e HTTPS/HTTP do proxy.
- Copie o código para um diretório permanente e mantenha `.env` fora do Git.
  Antes de usar um clone limpo, inclua as alterações ainda não commitadas no repositório.

Crie o `.env` a partir de `.env.example`, preenchendo pelo menos
`DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `DJANGO_ALLOWED_HOSTS` e
`DJANGO_CSRF_TRUSTED_ORIGINS`. Use uma chave Django aleatória e senhas exclusivas.
Exemplo para `app.exemplo.com.br`:

```dotenv
DJANGO_ALLOWED_HOSTS=app.exemplo.com.br
DJANGO_CSRF_TRUSTED_ORIGINS=https://app.exemplo.com.br
DJANGO_HTTPS_ENABLED=true
```

Preserve no `.env` as variáveis `DB_*` usadas pelo SQL Server legado.
`POSTGRES_PASSWORD` é exclusivamente para o banco da aplicação. O serviço
agendado de coleta só deve ser ativado depois de confirmar o acesso ao legado,
o SMTP e os destinatários.

Para SMTP, use porta 587 com `SMTP_USE_TLS=true` e `SMTP_USE_SSL=false`,
ou porta 465 com `SMTP_USE_TLS=false` e `SMTP_USE_SSL=true`. O host e a senha
dependem do provedor. Porta em branco usa 587, mas o envio ainda requer host
e senha válidos.

## 2. Proxy HTTPS

Configure o proxy para encaminhar a URL pública para
`http://127.0.0.1:8000`, preservando o cabeçalho `Host` e enviando
`X-Forwarded-Proto: https`. Os cookies seguros e o redirecionamento HTTPS
estão habilitados na configuração de produção. Certificados TLS e DNS são
geridos no proxy da VPS. HSTS inicia desabilitado (`0`); ative somente
quando o domínio e a renovação do certificado estiverem confirmados.

Não exponha `/app/media`, `/app/reports` nem o volume de backup pelo proxy.
Os relatórios são entregues pelas rotas autenticadas da aplicação.

## 3. Subir os serviços

Execute no diretório do projeto:

```bash
docker compose -f compose.production.yml up -d db redis
docker compose -f compose.production.yml build
docker compose -f compose.production.yml run --rm web python manage.py migrate
docker compose -f compose.production.yml up -d web worker
```

### Criar o primeiro Administrador

Depois que `migrate` terminar e o serviço `web` estiver em execução,
abra um terminal no diretório do projeto na VPS e execute:

```bash
docker compose -f compose.production.yml exec web python manage.py createsuperuser
```

O comando pede, nesta ordem, o nome de usuário, o e-mail, a senha e a
confirmação da senha. Digite uma senha forte; ela não aparece na tela.
Ao concluir, esse usuário recebe automaticamente o papel **Administrador**
e pode entrar em `https://SEU-DOMINIO/accounts/login/`. O endereço
`/users/` permite gerenciar outros usuários.

Informe um e-mail real para o Administrador caso ele deva receber relatórios.
Como o banco começa sem dados de clientes ou títulos, os estados CE/BA/PE
só aparecem para seleção após a primeira importação feita na VPS. Depois
de configurar o acesso ao SQL Server, execute uma coleta inicial:

```bash
docker compose -f compose.production.yml exec web python manage.py run_collection_pipeline
```

Confirme no terminal que a coleta trouxe títulos antes de prosseguir.
Depois dela, abra `/users/`, edite o Administrador e marque em
“Estados dos relatórios por e-mail” os estados desejados. Faça isso
antes de iniciar o `beat`, para o envio diário das 07:00 ter destinatário.

Os arquivos estáticos são coletados na imagem. O PostgreSQL inicia sem
registros da aplicação; `migrate` cria somente o esquema. O `db.sqlite3`
e os relatórios locais são excluídos da imagem. Os volumes persistem
PostgreSQL, Redis, mídia e relatórios; reiniciar ou reconstruir os contêineres
não remove os volumes.

Depois de configurar e validar SQL Server, SMTP e destinatários, ative a
coleta diária e as tarefas agendadas:

```bash
docker compose -f compose.production.yml up -d beat
```

O Beat dispara diariamente às 07:00 (`America/Sao_Paulo`): importa do
SQL Server, gera os seis relatórios (CE/BA/PE, vencidos/a vencer) e envia
os e-mails configurados. Se a coleta não trouxer dados, algum relatório
falhar ou o envio não for concluído, a tarefa registra falha. Apenas a
versão mais recente de cada estado e tipo permanece disponível.

## 4. Backup local

Cada execução do serviço de backup grava `postgres.dump`, `files.tar.gz`
(mídia e relatórios) e `COMPLETE` no volume `cred-cobr_backups_data`.
O marcador `COMPLETE` só existe após a finalização dos dois arquivos.

```bash
docker compose -f compose.production.yml --profile tools run --rm backup
```

Agende esse comando no cron do host quando escolher o horário. Os backups
ficam somente na VPS e não são apagados automaticamente; acompanhe o espaço
em disco. Uma cópia em armazenamento externo deve ser acrescentada quando
houver essa possibilidade. A rotina antiga do Celery, que copiava apenas
mídia em instalações PostgreSQL, fica desativada em produção.

Antes de atualizações ou migrações futuras, gere um backup e confirme o
marcador `COMPLETE`. Guarde também o `.env` em local seguro separado do
repositório.

## 5. Verificação pendente

A validação final depende da VPS e do IP dedicado: inicialização dos serviços,
migrações, login, HTTPS, acesso ao SQL Server, SMTP, geração/download de
relatórios e criação/restauração de backup. Execute-a quando houver
autorização e acesso ao ambiente.
