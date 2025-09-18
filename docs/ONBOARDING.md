# Onboarding & SOP

## Auth (JWT)
- Obtain token: `POST /api/auth/token/` with JSON `{ "username": "...", "password": "..." }`.
- Refresh: `POST /api/auth/token/refresh/`.
- Default access token lifetime: 30 minutes.

## Roles & Lookups
- PM / Concierge: full access to lookups and reports.
- Owner / Agent: only for units they have `UnitAccess` to.
- Lookups:
  - `GET /api/units/{id}/parking`
  - `GET /api/spots/{id}/unit`

## CSV Import/Export
- Export: `GET /api/assignments/export.csv` (PM only).
- Latest Nightly: `GET /api/assignments/latest.csv` (PM only).
- Import: `POST /api/assignments/import.csv?dry_run=1|0` with `multipart/form-data` and `file=<csv>`.
- Uploaded CSVs are stored at `MEDIA_ROOT/imports/assignments_uploaded_<ts>.csv`.
- Import errors (non-dry) saved to `MEDIA_ROOT/import_errors/*.csv`.

## Cron
- List: `python manage.py crontab show`
- Add: `python manage.py crontab add`
- Nightly export job: `core.cron.nightly_export_and_cleanup` (02:15 UTC)
- Hourly reminders: `core.cron.email_reminders_checkins_outs`
- Manual check: run `python manage.py shell` and call the job once if needed.

## Backup/Restore (SQLite dev)
- DB file: `db.sqlite3`
- Backup: `cp db.sqlite3 backups/db-$(date +%F).sqlite3`
- Restore: `cp backups/db-YYYY-MM-DD.sqlite3 db.sqlite3 && python manage.py migrate`

## Postgres (docker-compose)
- Start: `docker compose up -d --build`
- Migrate: `docker compose exec web python manage.py migrate`
- Seed: `docker compose exec web python manage.py load_sample_data`

## Token & Secret Rotation
- Update `.env` or environment variables:
  - `SECRET_KEY`, JWT lifetimes (if needed)
- Restart the process/container after rotation.

## Ops Page
- Staff-only helper: `GET /api/ops/` → (served at `/api/ops/` under `core/ops.html`)
- Upload CSV and run reports without a build pipeline.
