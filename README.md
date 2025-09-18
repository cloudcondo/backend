# Condo Backend

A Django/DRF service for condo parking assignments and guest bookings.

## Quick start (dev / Codespaces)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
