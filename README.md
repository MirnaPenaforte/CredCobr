# CRED-COBR

Aplicacao Django para automacao de relatorios e gestao de cobranca.

## Desenvolvimento

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

O banco local padrao e SQLite. Para PostgreSQL, defina `DATABASE_URL` e execute o banco com `docker compose up -d db`.

## Testes

```powershell
pytest
python manage.py check
```

Credenciais, tokens e senhas devem ser fornecidos por variaveis de ambiente.
