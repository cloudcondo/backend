from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings

from core.services.csv_roundtrip import write_assignments_export


def nightly_export_and_cleanup() -> None:
    """
    Create a timestamped assignments CSV and prune old files.
    """
    export_dir = Path(getattr(settings, "ASSIGNMENTS_EXPORT_DIR", "exports"))
    export_dir.mkdir(parents=True, exist_ok=True)

    # write new export
    path = write_assignments_export()
    print(f"wrote {path}")

    # retention (days); default 14
    days = int(getattr(settings, "ASSIGNMENTS_EXPORT_RETENTION_DAYS", 14))
    cutoff = datetime.utcnow() - timedelta(days=days)
    for p in export_dir.glob("assignments_*.csv"):
        if datetime.utcfromtimestamp(p.stat().st_mtime) < cutoff:
            try:
                p.unlink()
                print(f"deleted old export {p}")
            except Exception as e:
                print(f"warn: failed to delete {p}: {e}")


def email_reminders_checkins_outs() -> None:
    """
    Placeholder for hourly reminders job; implement your logic here.
    """
    print("hourly reminders tick")
