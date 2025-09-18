from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.services.csv_assignments import import_assignments_csv


class Command(BaseCommand):
    help = "Import/Upsert Unit↔Parking assignments from CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV file")

    def handle(self, *args, **opts):
        p = Path(opts["csv_path"])
        if not p.exists():
            raise CommandError(f"File not found: {p}")
        changed, warnings = import_assignments_csv(p.read_text(encoding="utf-8"))
        for w in warnings:
            self.stderr.write(w)
        self.stdout.write(self.style.SUCCESS(f"Imported/updated rows: {changed}"))
