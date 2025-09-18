import csv
import io
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from django.db import transaction

from core.models import Condo, ParkingSpot, Unit, UnitParkingAssignment

CSV_FIELDS_EXPORT = [
    "condo_code",
    "unit_number",
    "parking_code",
    "status",  # derived: active / inactive
    "effective_start",
    "effective_end",
]

# We’ll accept either start_date/end_date OR effective_start/effective_end on import
CSV_FIELDS_IMPORT_ALLOWED = {
    "condo_code",
    "unit_number",
    "parking_code",
    "is_primary",
    "start_date",
    "end_date",
    "effective_start",
    "effective_end",
    "status",  # ignored if present (we compute it)
}


def _parse_date(val: str):
    """
    Accepts: YYYY-MM-DD, empty/None. Returns date or None.
    """
    if not val:
        return None
    val = str(val).strip()
    if not val:
        return None
    # try ISO format first
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        # last resort: let fromisoformat try (can raise)
        return date.fromisoformat(val)


def export_assignments_to_csv() -> Tuple[str, bytes]:
    """
    Build a canonical CSV of current assignments.

    Columns:
      condo_code, unit_number, parking_code, status, effective_start, effective_end
    - status is computed: 'active' if end is None or >= today; else 'inactive'
    """
    rows: List[List[str]] = []
    today = date.today()

    # Select related for speed
    qs = UnitParkingAssignment.objects.select_related(
        "unit__condo", "parking_spot__condo"
    ).order_by(
        "unit__condo__code",
        "unit__unit_number",
        "parking_spot__code",
        "start_date",
    )

    for a in qs:
        condo_code = a.unit.condo.code  # unit & spot share condo by validation
        unit_number = a.unit.unit_number
        parking_code = a.parking_spot.code
        eff_start = a.start_date.isoformat() if a.start_date else ""
        eff_end = a.end_date.isoformat() if a.end_date else ""
        is_active = (a.end_date is None) or (a.end_date >= today)
        status = "active" if is_active else "inactive"

        rows.append([condo_code, unit_number, parking_code, status, eff_start, eff_end])

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(CSV_FIELDS_EXPORT)
    writer.writerows(rows)

    content_bytes = buffer.getvalue().encode("utf-8")
    filename = "assignments.csv"
    return filename, content_bytes


@transaction.atomic
def import_assignments_from_csv(uploaded_file) -> Dict[str, Any]:
    """
    Upsert assignments from a CSV file.

    Accepted headers (case-sensitive):
      required: condo_code, unit_number, parking_code
      optional: is_primary, start_date, end_date OR effective_start, effective_end
      optional: status (ignored; we compute status from dates)

    Behavior:
      - For (condo_code, unit_number, parking_code) find related models.
      - If a UnitParkingAssignment with that (unit, parking_spot) exists, update fields.
      - Else create a new assignment.
      - We do NOT delete/archive missing rows in this basic import (keeps it safe).

    Returns:
      {
        "created": int,
        "updated": int,
        "errors": int,
        "error_rows": [ {"row_number": n, "error": "...", "row": {...}}, ... ],
        "total_rows": int
      }
    """
    # Handle InMemoryUploadedFile / TemporaryUploadedFile and plain file-like objects
    if hasattr(uploaded_file, "read"):
        raw = uploaded_file.read()
        if isinstance(raw, bytes):
            text = raw.decode("utf-8-sig")
        else:
            text = raw
    else:
        # If someone passed us path or bytes
        text = (
            uploaded_file.decode("utf-8-sig")
            if isinstance(uploaded_file, (bytes, bytearray))
            else str(uploaded_file)
        )

    f = io.StringIO(text)
    reader = csv.DictReader(f)

    # Validate headers
    field_set = set(reader.fieldnames or [])
    missing = {"condo_code", "unit_number", "parking_code"} - field_set
    if missing:
        return {
            "created": 0,
            "updated": 0,
            "errors": 1,
            "error_rows": [
                {
                    "row_number": 0,
                    "error": f"Missing required columns: {', '.join(sorted(missing))}",
                    "row": {},
                }
            ],
            "total_rows": 0,
        }

    # Extra unknown fields? Not fatal; we simply ignore them.
    # (No temp variables here to satisfy flake8 F841.)
    # unknown = field_set - CSV_FIELDS_IMPORT_ALLOWED  # ignored

    created = 0
    updated = 0
    errors = 0
    error_rows: List[Dict[str, Any]] = []
    total = 0

    for idx, row in enumerate(reader, start=2):  # header is line 1
        total += 1
        try:
            condo_code = (row.get("condo_code") or "").strip()
            unit_number = (row.get("unit_number") or "").strip()
            parking_code = (row.get("parking_code") or "").strip()
            is_primary_raw = (row.get("is_primary") or "").strip()

            # pick date fields from either {start_date,end_date} or {effective_start,effective_end}
            start_raw = (
                row.get("start_date") or row.get("effective_start") or ""
            ).strip()
            end_raw = (row.get("end_date") or row.get("effective_end") or "").strip()

            if not (condo_code and unit_number and parking_code):
                raise ValueError("condo_code, unit_number, parking_code are required")

            try:
                condo = Condo.objects.get(code=condo_code)
            except Condo.DoesNotExist:
                raise ValueError(f"Condo not found: code={condo_code}")

            try:
                unit = Unit.objects.get(condo=condo, unit_number=unit_number)
            except Unit.DoesNotExist:
                raise ValueError(
                    f"Unit not found: condo={condo_code} unit_number={unit_number}"
                )

            try:
                spot = ParkingSpot.objects.get(condo=condo, code=parking_code)
            except ParkingSpot.DoesNotExist:
                raise ValueError(
                    f"Parking spot not found: condo={condo_code} code={parking_code}"
                )

            # parse flags/dates
            is_primary = None
            if is_primary_raw != "":
                is_primary = str(is_primary_raw).lower() in {
                    "1",
                    "true",
                    "yes",
                    "y",
                    "t",
                }

            start_date = _parse_date(start_raw) if start_raw else None
            end_date = _parse_date(end_raw) if end_raw else None

            # upsert by (unit, parking_spot)
            obj, existed = UnitParkingAssignment.objects.get_or_create(
                unit=unit,
                parking_spot=spot,
                defaults={
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_primary": bool(is_primary) if is_primary is not None else False,
                },
            )
            if existed:
                created += 1
            else:
                changed = False
                # Only update fields that were provided (leave others intact)
                if start_date is not None and obj.start_date != start_date:
                    obj.start_date = start_date
                    changed = True
                if end_date is not None and obj.end_date != end_date:
                    obj.end_date = end_date
                    changed = True
                if is_primary is not None and obj.is_primary != bool(is_primary):
                    obj.is_primary = bool(is_primary)
                    changed = True
                if changed:
                    obj.save(update_fields=["start_date", "end_date", "is_primary"])
                    updated += 1

        except Exception as e:
            errors += 1
            error_rows.append(
                {
                    "row_number": idx,
                    "error": str(e),
                    "row": row,
                }
            )

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "error_rows": error_rows,
        "total_rows": total,
    }
