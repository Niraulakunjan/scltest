# Django School Management System

Role-based school management system with dedicated portals for:
- Admin
- Student
- Parent

Main highlight implemented: **QR Attendance System**
- Student portal shows a signed QR code.
- Admin portal opens device camera and scans student QR.
- Attendance is marked server-side and duplicate scans are prevented per day.

## Features

### Admin Portal
- Dashboard with student, attendance, class, and fee stats
- Student account/profile creation
- Parent account/profile creation
- Notice publishing
- Homework assignment
- Fee record management
- QR attendance scanner + manual fallback

### Student Portal
- Personal dashboard
- Signed attendance QR code
- Attendance history
- Notices and homework
- Fee status

### Parent Portal
- Child selection (supports multiple linked children)
- Child attendance history
- Fee records
- Parent-facing notices

## Tech Stack
- Django 6
- SQLite
- HTML/CSS/JS templates
- `html5-qrcode` (camera scanning)
- `qrcode` (local QR image generation in student portal)

## Environment Variables

Copy `.env.example` and set values for your deployment.

- `DJANGO_DEBUG` (`0` for production)
- `DJANGO_SECRET_KEY` (required when `DJANGO_DEBUG=0`)
- `DJANGO_ALLOWED_HOSTS` (comma-separated hostnames)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated `https://...` origins)
- `DJANGO_SECURE_SSL_REDIRECT` (`1` by default in production)

## Local Development

```bash
python3 -m pip install -r requirements.txt
export DJANGO_DEBUG=1
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

Open: `http://127.0.0.1:8000/`

## Production Checklist

```bash
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py check --deploy
```

- Set `DJANGO_DEBUG=0`
- Set strong `DJANGO_SECRET_KEY`
- Set `DJANGO_ALLOWED_HOSTS`
- Set `DJANGO_CSRF_TRUSTED_ORIGINS`
- Serve behind HTTPS + reverse proxy

## Important URLs
- App login: `/`
- Django admin site: `/site-admin/`
# scltest
