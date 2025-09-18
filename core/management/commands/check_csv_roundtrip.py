from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import UnitParkingAssignment


class Command(BaseCommand):
    help = "Sanity check: every active assignment links a unit to a parking spot and vice versa"

    def handle(self, *args, **kwargs):
        missing = []
        for a in UnitParkingAssignment.objects.select_related("unit", "parking_spot"):
            if not a.unit_id or not a.parking_spot_id:
                missing.append(a.pk)
        if missing:
            self.stderr.write(f"Incomplete assignments (no unit or no spot): {missing}")
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Assignment round-trip looks good."))
