# core/cron.py
import os
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import ShortTermBooking
from .services.csv_roundtrip import export_assignments_csv_text  # defined below


def nightly_export_and_cleanup():
    base = Path(getattr(settings, "ASSIGNMENTS_EXPORT_DIR", "exports"))
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d")
    out = base / f"assignments_{ts}.csv"
    out.write_text(export_assignments_csv_text(), encoding="utf-8")

    # retention
    keep_days = int(getattr(settings, "ASSIGNMENTS_EXPORT_RETENTION_DAYS", 14))
    cutoff = timezone.now() - timedelta(days=keep_days)
    for p in base.glob("assignments_*.csv"):
        # naive parse: assignments_YYYYMMDD.csv
        try:
            d = datetime.strptime(p.stem.split("_")[1], "%Y%m%d")
            if d < cutoff.replace(tzinfo=None):
                p.unlink(missing_ok=True)
        except Exception:
            continue


def email_reminders_checkins_outs():
    today = timezone.localdate()
    soon = today + timedelta(days=1)
    qs_in = ShortTermBooking.objects.filter(check_in=today, status="approved")
    qs_out = ShortTermBooking.objects.filter(check_out=soon, status="approved")
    # This is a stub. Replace send_mail with your email backend/config.
    for b in qs_in:
        send_mail(
            subject=f"Reminder: Guest checking in today for {b.unit}",
            message=f"Guest {b.guest_first_name} {b.guest_last_name} — plate {b.vehicle_plate or 'n/a'}",
            from_email=os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[os.getenv("REMINDER_TO_EMAIL", "ops@example.com")],
            fail_silently=True,
        )
    for b in qs_out:
        send_mail(
            subject=f"Reminder: Guest checks out tomorrow for {b.unit}",
            message=f"Booking {b.id} ends {b.check_out.isoformat()}",
            from_email=os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[os.getenv("REMINDER_TO_EMAIL", "ops@example.com")],
            fail_silently=True,
        )
