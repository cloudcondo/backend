from datetime import datetime
from pathlib import Path
from typing import Tuple

from django.conf import settings

from core.services.csv_assignments import export_assignments_to_csv


def export_assignments_csv_text() -> str:
    """
    Return the CSV export as a UTF-8 string (not a tuple).
    """
    _filename, content_bytes = export_assignments_to_csv()
    return content_bytes.decode("utf-8")


def write_assignments_export(now: datetime | None = None) -> Path:
    """
    Write a timestamped CSV into ASSIGNMENTS_EXPORT_DIR and return the path.
    """
    export_dir = Path(getattr(settings, "ASSIGNMENTS_EXPORT_DIR", "exports"))
    export_dir.mkdir(parents=True, exist_ok=True)
    ts = (now or datetime.utcnow()).strftime("%Y%m%dT%H%M%SZ")
    out_path = export_dir / f"assignments_{ts}.csv"
    out_path.write_text(export_assignments_csv_text(), encoding="utf-8")
    return out_path
