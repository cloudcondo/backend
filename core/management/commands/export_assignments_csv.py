from pathlib import Path

from django.core.management.base import BaseCommand

from core.services.csv_assignments import export_all_assignments


class Command(BaseCommand):
    help = "Export Unit↔Parking assignments to CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out", default="exports/assignments.csv", help="Output CSV path"
        )

    def handle(self, *args, **opts):
        out = Path(opts["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        csv_text = export_all_assignments()
        out.write_text(csv_text, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {out} ({len(csv_text)} bytes)"))
