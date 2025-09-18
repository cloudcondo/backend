# core/services/csv_assignments.py
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

# We accept either start_date/end_date OR effective_start/effective_end on import
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
    if not val:
        return None
    val = str(val).strip()
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
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

    qs = UnitParkingAssignment.objects.select_related(
        "unit__condo", "parking_spot__condo"
    ).order_by(
        "unit__condo__code", "unit__unit_number", "parking_spot__code", "start_date"
    )

    for a in qs:
        condo_code = a.unit.condo.code
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


def _errors_to_csv(error_rows: List[Dict[str, Any]]) -> str:
    sio = io.StringIO(newline="")
    fieldnames = ["row_number", "error", "condo_code", "unit_number", "parking_code"]
    writer = csv.DictWriter(sio, fieldnames=fieldnames)
    writer.writeheader()
    for r in error_rows:
        row = r.get("row", {}) or {}
        writer.writerow(
            {
                "row_number": r.get("row_number"),
                "error": r.get("error"),
                "condo_code": (row.get("condo_code") or "").strip(),
                "unit_number": (row.get("unit_number") or "").strip(),
                "parking_code": (row.get("parking_code") or "").strip(),
            }
        )
    return sio.getvalue()


@transaction.atomic
def import_assignments_from_csv(uploaded_file, dry_run: bool = False) -> Dict[str, Any]:
    """
    Upsert assignments from a CSV file.

    Accepted headers (case-sensitive):
      required: condo_code, unit_number, parking_code
      optional: is_primary, start_date, end_date OR effective_start, effective_end
      optional: status (ignored; computed)

    When dry_run=True:
      - perform full validation
      - return the same structure but do NOT write any DB changes
    """
    # read file payload
    if hasattr(uploaded_file, "read"):
        raw = uploaded_file.read()
        text = (
            raw.decode("utf-8-sig") if isinstance(raw, (bytes, bytearray)) else str(raw)
        )
    else:
        text = (
            uploaded_file.decode("utf-8-sig")
            if isinstance(uploaded_file, (bytes, bytearray))
            else str(uploaded_file)
        )

    f = io.StringIO(text)
    reader = csv.DictReader(f)

    field_set = set(reader.fieldnames or [])
    missing = {"condo_code", "unit_number", "parking_code"} - field_set
    if missing:
        errors = [
            {
                "row_number": 0,
                "error": f"Missing required columns: {', '.join(sorted(missing))}",
                "row": {},
            }
        ]
        return {
            "created": 0,
            "updated": 0,
            "errors": len(errors),
            "error_rows": errors,
            "total_rows": 0,
            "errors_csv": _errors_to_csv(errors),
        }

    created = 0
    updated = 0
    errors = 0
    error_rows: List[Dict[str, Any]] = []
    total = 0

    # Keep explicit lists of write ops when not dry_run
    pending_updates: List[UnitParkingAssignment] = []
    pending_creates: List[UnitParkingAssignment] = []

    for idx, row in enumerate(reader, start=2):  # header is line 1
        total += 1
        try:
            condo_code = (row.get("condo_code") or "").strip()
            unit_number = (row.get("unit_number") or "").strip()
            parking_code = (row.get("parking_code") or "").strip()
            is_primary_raw = (row.get("is_primary") or "").strip()

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

            obj, created_now = UnitParkingAssignment.objects.get_or_create(
                unit=unit,
                parking_spot=spot,
                defaults={
                    "start_date": start_date or date.today(),
                    "end_date": end_date,
                    "is_primary": bool(is_primary) if is_primary is not None else False,
                },
            )
            if created_now:
                # new row
                created += 1
                if not dry_run:
                    pending_creates.append(obj)
            else:
                # existing: apply changes if any
                changed = False
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
                    updated += 1
                    if not dry_run:
                        pending_updates.append(obj)

        except Exception as e:
            errors += 1
            error_rows.append({"row_number": idx, "error": str(e), "row": row})

    # Apply writes if not dry_run
    if not dry_run:
        # obj from get_or_create is already in DB when created_now=True, so
        # pending_creates is informational only; we still ensure updates are saved.
        for obj in pending_updates:
            obj.save(update_fields=["start_date", "end_date", "is_primary"])

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "error_rows": error_rows,
        "total_rows": total,
        "errors_csv": _errors_to_csv(error_rows) if errors else "",
    }
