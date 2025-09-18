# core/services/csv_roundtrip.py
import csv
from io import StringIO

from .models import UnitParkingAssignment

CSV_HEADERS = [
    "condo_code",
    "unit_number",
    "spot_code",
    "start_date",
    "end_date",
    "is_primary",
]


def export_assignments_csv_text() -> str:
    out = StringIO()
    w = csv.writer(out)
    w.writerow(CSV_HEADERS)
    qs = UnitParkingAssignment.objects.select_related(
        "unit__condo", "parking_spot__condo"
    ).order_by("unit__condo__code", "unit__unit_number", "-start_date")
    for a in qs:
        w.writerow(
            [
                a.unit.condo.code,
                a.unit.unit_number,
                a.parking_spot.code,
                a.start_date.isoformat(),
                a.end_date.isoformat() if a.end_date else "",
                str(a.is_primary).lower(),
            ]
        )
    return out.getvalue()
