import os

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = [value.strip() for value in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if value.strip()]
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if value.strip()]

if SECRET_KEY == "django-insecure-development-only" or not SECRET_KEY:
    raise RuntimeError("Defina DJANGO_SECRET_KEY para produção")
if not ALLOWED_HOSTS:
    raise RuntimeError("Defina DJANGO_ALLOWED_HOSTS para produção")
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    raise RuntimeError("Configure APP_DATABASE_HOST ou DATABASE_URL para produção")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("DJANGO_HTTPS_ENABLED", "true").lower() == "true"
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0")) if SECURE_SSL_REDIRECT else 0

# O backup de produção inclui PostgreSQL e arquivos pelo serviço dedicado do Compose.
CELERY_BEAT_SCHEDULE = {
    name: task for name, task in CELERY_BEAT_SCHEDULE.items() if name != "daily-backup"
}
