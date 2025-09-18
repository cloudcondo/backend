# core/management/commands/ci_dry_run_import_check.py
import csv
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from accounts.models import UserProfile
from core.models import Condo, ParkingSpot, Unit


class Command(BaseCommand):
    help = "CI smoke: POST /api/assignments/import.csv?dry_run=1 and assert counts in JSON response."

    def handle(self, *args, **opts):
        # Make sure we have at least one condo/unit/spot (fixtures/seeded in CI)
        condo = Condo.objects.first()
        unit = Unit.objects.filter(condo=condo).first() if condo else None
        spot = ParkingSpot.objects.filter(condo=condo).first() if condo else None
        if not (condo and unit and spot):
            raise CommandError(
                "Missing seeded data (condo/unit/spot). Load fixtures first."
            )

        # Build minimal CSV in memory
        mem = BytesIO()
        writer = csv.writer(mem)
        writer.writerow(
            [
                "condo_code",
                "unit_number",
                "parking_code",
                "status",
                "effective_start",
                "effective_end",
            ]
        )
        writer.writerow([condo.code, unit.unit_number, spot.code, "active", "", ""])
        mem.seek(0)
        mem.name = "assignments.csv"  # DRF uses .name to infer filename

        # Create a PM user (so endpoint is authorized)
        U = get_user_model()
        pm, _ = U.objects.get_or_create(
            username="ci-pm", defaults={"email": "ci-pm@example.com", "is_staff": True}
        )
        prof, _ = UserProfile.objects.get_or_create(user=pm)
        prof.role = "pm"
        prof.save()

        client = APIClient()
        client.force_authenticate(user=pm)
        resp = client.post(
            "/api/assignments/import.csv?dry_run=1",
            data={"file": mem},
            format="multipart",
        )
        if resp.status_code != 200:
            raise CommandError(
                f"Import endpoint failed: {resp.status_code} {resp.content!r}"
            )

        data = resp.json()
        # We expect at least one processed row and no crash
        if "total_rows" not in data or data["total_rows"] < 1:
            raise CommandError(f"Unexpected response: {data}")
        # Accepted keys present
        for key in ["created", "updated", "errors", "dry_run"]:
            if key not in data:
                raise CommandError(f"Missing key '{key}' in response: {data}")

        self.stdout.write(self.style.SUCCESS("CI dry-run CSV import check passed."))
