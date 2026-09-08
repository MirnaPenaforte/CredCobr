$ErrorActionPreference = "Stop"

& ".\.venv\Scripts\pytest.exe" -q
& ".\.venv\Scripts\python.exe" manage.py check
& ".\.venv\Scripts\python.exe" manage.py makemigrations --check --dry-run
