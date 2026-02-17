# Deploy This Django App on cPanel (Production)

This guide is for deploying this project (`manage.py` at repo root, `schoolms/wsgi.py`) on cPanel using Passenger.

## 1) Prerequisites

- cPanel account with either:
  - `Setup Python App` (CloudLinux Python Selector), or
  - `Application Manager` (Passenger)
- Python version compatible with your server (use latest available stable)
- SSH/Terminal access in cPanel
- SSL enabled for your domain

## 2) Upload Project

- Upload project files to your account, for example:
  - `/home/CPANEL_USER/schoolms`
- Do not upload local virtualenv or local DB dumps.

## 3) Create Python App in cPanel

In cPanel:

- Open `Setup Python App` (or `Application Manager`)
- Create app with values like:
  - Python version: `3.x`
  - Application root: `schoolms`
  - Application URL: your domain (or sub-path)
  - Startup file: `passenger_wsgi.py`
  - Entry point: `application`

After creation, copy the activation command shown by cPanel (it includes the correct virtualenv path).

## 4) Install Dependencies

Run in cPanel Terminal/SSH:

```bash
cd /home/CPANEL_USER/schoolms
source /home/CPANEL_USER/virtualenv/schoolms/3.x/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5) Configure Environment Variables (Required)

In cPanel Python App -> Environment Variables, add:

- `DJANGO_DEBUG=0`
- `DJANGO_SECRET_KEY=<long-random-secret>`
- `DJANGO_ALLOWED_HOSTS=example.com,www.example.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com`
- `DJANGO_SECURE_SSL_REDIRECT=1`

Use values matching your real domain.

## 6) Configure `passenger_wsgi.py`

Create/update `/home/CPANEL_USER/schoolms/passenger_wsgi.py`:

```python
import os
import sys

PROJECT_HOME = "/home/CPANEL_USER/schoolms"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolms.settings")

from schoolms.wsgi import application
```

If cPanel generated this file automatically, keep the virtualenv/interpreter lines it adds and only ensure `DJANGO_SETTINGS_MODULE` and `from schoolms.wsgi import application` are correct.

## 7) Run Django Production Commands

```bash
cd /home/CPANEL_USER/schoolms
source /home/CPANEL_USER/virtualenv/schoolms/3.x/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
python manage.py createsuperuser
```

## 8) Restart Application

- Use `Restart` in cPanel Python App UI, or
- touch restart file:

```bash
touch /home/CPANEL_USER/schoolms/tmp/restart.txt
```

## 9) Verify

- App URL loads over `https`
- Admin panel works: `/site-admin/`
- Static file test opens in browser:
  - `https://your-domain.com/static/css/app.css`

## 10) Common Issues

- `DisallowedHost`:
  - fix `DJANGO_ALLOWED_HOSTS`
- CSRF failures on login/forms:
  - fix `DJANGO_CSRF_TRUSTED_ORIGINS` with `https://...`
- 500 error after code update:
  - restart app and re-check `passenger_wsgi.py`
- Missing static files:
  - re-run `collectstatic --noinput` and restart

## Official References

- cPanel: How to Install a Python WSGI Application (updated Dec 9, 2025)
  - https://docs.cpanel.net/knowledge-base/web-services/how-to-install-a-python-wsgi-application/
- cPanel: Using Passenger Applications (updated Dec 10, 2025)
  - https://docs.cpanel.net/knowledge-base/web-services/using-passenger-applications/
- cPanel support: register app with Python Selector
  - https://support.cpanel.net/hc/en-us/articles/360057849753-How-to-register-an-application-with-Python-Selector
