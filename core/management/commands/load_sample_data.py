from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Load sample data fixtures for local/CI runs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true", help="Flush DB before loading fixtures"
        )

    def handle(self, *args, **opts):
        core_path = Path(apps.get_app_config("core").path)
        fixture_path = core_path / "fixtures" / "sample_data.json"
        if not fixture_path.exists():
            raise CommandError(f"Fixture not found: {fixture_path}")

        if opts["flush"]:
            self.stdout.write("Flushing database...")
            call_command("flush", interactive=False)

        self.stdout.write(f"Loading fixture: {fixture_path}")
        call_command("loaddata", str(fixture_path))
        self.stdout.write(self.style.SUCCESS("Sample data loaded."))
