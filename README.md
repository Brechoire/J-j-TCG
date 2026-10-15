# WikiCards — jeu de collection encyclopédique (MVP)

Collectionnez des cartes Football issues de Wikidata/Wikipédia, ouvrez un booster gratuit toutes les 10 minutes (5 cartes distinctes), complétez l'album, revendez les doublons. Aucun argent réel. Interface mobile-first (nav basse), Django Templates + HTMX.

Stack : Python 3.12+, **Django 5.2 LTS**, SQLite dev / PostgreSQL prod, Tailwind compilé local, pytest-django, Ruff, pre-commit, GitHub Actions.

Docs : `docs/` (PRD, ARCHITECTURE, DATABASE, GAME_RULES, ECONOMY, RARITY_SYSTEM, WIKIDATA_IMPORT, SECURITY, TESTING, DEPLOYMENT). Backlog : `PROJECT_TASKS.md`.

## Prérequis

- Python 3.12, Node 18+ (Tailwind), Git.
- Linux Mint / Windows (WSL recommandé sous Windows).

## Installation (dev)

```bash
git clone <VOTRE_REPO> wikicards && cd wikicards
python3 -m venv env
# Linux Mint :
source env/bin/activate
# Windows PowerShell :
# .\env\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

## Générer une clé Django (obligatoire en prod)

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Collez la valeur dans `.env` → `DJANGO_SECRET_KEY=...`. En dev la clé peut rester vide (fallback local). Avec `DJANGO_DEBUG=0`, une clé absente ou `django-insecure-*` bloque le démarrage (sécurité).

## Config `.env`

```ini
DJANGO_SECRET_KEY=<clé-générée>
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
```

Prod : `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS=votre-domaine`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://votre-domaine`, `DATABASE_URL=postgres://USER:PASS@HOST:5432/DB`.

## Base + lancement

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py test          # 41 tests attendus
npm install
npm run build:css              # régénère static/css/output.css (ignoré par git)
python manage.py runserver
```

Ouvrez `http://127.0.0.1:8000/` → bouton **Ouvrir un booster gratuit** (collection Football). Connectez-vous d'abord (`/comptes/inscription/`).

## Import Football (100 cartes)

```bash
python manage.py import_wikidata football --limit 100 --dry-run   # sans réseau écrit rien
python manage.py import_wikidata football --limit 100
python manage.py import_wikidata football --qid Q42               # réimport une entité
```

Robuste : lots de 50, User-Agent identifiable, timeout 10s, backoff ×3, progression tous les 10, reprise partielle, anti-doublons, rareté auto 55/25/12/6/2 (verrous admin préservés).

## Commandes utiles

```bash
ruff check . && ruff format --check .
pytest -q
python manage.py check
python manage.py check --deploy   # 6 warnings dev attendus (HSTS/cookies/DEBUG) ; verts en prod via env
pre-commit install
```

## Publier sur GitHub

```bash
git init
git add .
git commit -m "feat: WikiCards MVP phases 0-5"
gh repo create wikicards --private --source=. --push
# ou sans gh :
# git remote add origin git@github.com:VOTRE_COMPTE/wikicards.git
# git branch -M main && git push -u origin main
```

Ne sont **jamais** commités (`.gitignore`) : `.env`, `db.sqlite3`, `env/`, `node_modules/`, `static/css/output.css`, caches. Vérifiez avant push : `git status --short` et `git check-ignore -v .env db.sqlite3 env node_modules`.

## Sécurité

CSRF, auth UUID, permissions admin-only, validation serveur (prix/valeurs jamais depuis le navigateur), XSS auto-escape, idempotence anti double-débit, audit `WalletTransaction`, secrets en env uniquement. Détails : `docs/SECURITY.md`. Données Wikimedia : attributions conservées et affichées (CC BY-SA et licences Commons).
