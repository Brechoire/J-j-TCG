# Déploiement

## Dev (Windows + Linux Mint)

```bash
python -m venv env
./env/bin/pip install -r requirements.txt
./env/bin/python manage.py migrate
./env/bin/python manage.py runserver
```

Tailwind local : `npm ci && npm run build:css` (à ajouter Phase 1), `collectstatic` en prod uniquement.

## Prod

- `DATABASE_URL=postgres://...`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- PostgreSQL 15+, `migrate`, `collectstatic`, Gunicorn + Nginx/HTTPS, backups quotidiens.
- Docker Compose optionnel : `web` (gunicorn) + `db` (postgres) + volume médias. Pas de Redis/Celery sans justification.

## Vérif

`manage.py check --deploy`, `pytest -q`, Playwright smoke, logs sans secret.
