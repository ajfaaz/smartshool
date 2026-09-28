# SmartSchool Deployment Guide

This repository contains the full production-ready SmartSchool ERP application setup.

## Workflow

1. Edit locally
2. Test locally: `python manage.py check`
3. Commit and push to GitHub: `git push origin main`
4. Deploy to production cPanel

## Local Workflow

Run locally:
```powershell
python manage.py runserver
```

System check before pushing:
```powershell
python manage.py check
```

## cPanel & Production Environment Settings

Recommended production `.env` settings:

- `DEBUG=False`
- `SECRET_KEY=<production secret key>`
- `ALLOWED_HOSTS=smartschool.arewanetventures.com,.arewanetventures.com,127.0.0.1`
- `CSRF_TRUSTED_ORIGINS=https://smartschool.arewanetventures.com,https://*.arewanetventures.com`
- `DEFAULT_FROM_EMAIL=infor@arewanetventures.com`

## Deployment Script (`deploy.sh`)

Run on server via SSH:
```bash
bash /home/jvlbvywb/repositories/smartschool/deploy.sh
```

It executes the following steps:
1. Pulls latest code from GitHub `main` branch.
2. Syncs updated application files to `/home/jvlbvywb/smartschool/`.
3. Preserves server-only configuration (`.env`, `db.sqlite3`, `media/`, `staticfiles/`).
4. Installs requirements via `pip install -r requirements.txt`.
5. Runs Django database migrations: `python manage.py migrate --noinput`.
6. Collects static assets: `python manage.py collectstatic --noinput`.
7. Restarts the Passenger WSGI application (`touch tmp/restart.txt`).
