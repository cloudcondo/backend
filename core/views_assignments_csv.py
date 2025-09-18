# core/views_assignments_csv.py
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedJWT, IsPropertyManager

from .services.csv_assignments import (
    export_assignments_to_csv,
    import_assignments_from_csv,
)


@extend_schema(tags=["Assignments"])
class AssignmentsCSVExportView(APIView):
    # PM only
    permission_classes = [IsAuthenticatedJWT & IsPropertyManager]

    def get(self, request):
        filename, content = export_assignments_to_csv()
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@extend_schema(tags=["Assignments"])
class AssignmentsCSVImportView(APIView):
    """
    POST multipart/form-data with 'file'.
    Optional query: ?dry_run=1
    Returns JSON summary and, if errors, a link to an error CSV file when not dry_run.
    Also persists the uploaded CSV to MEDIA_ROOT/imports when not dry_run.
    """

    # PM only
    permission_classes = [IsAuthenticatedJWT & IsPropertyManager]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        dry_run = str(request.query_params.get("dry_run", "0")).lower() in {
            "1",
            "true",
            "yes",
            "y",
        }
        # Persist a copy of what was uploaded (for audit) when not dry_run
        if not dry_run:
            media_root = Path(getattr(settings, "MEDIA_ROOT", "media"))
            up_dir = media_root / "imports"
            up_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            up_path = up_dir / f"assignments_uploaded_{ts}.csv"
            # Save raw bytes from InMemoryUploadedFile
            file.seek(0)
            up_path.write_bytes(file.read())
            # Reset pointer for the actual import routine
            file.seek(0)

        result = import_assignments_from_csv(file, dry_run=dry_run)

        errors_path = ""
        if result.get("errors") and not dry_run:
            media_root = Path(getattr(settings, "MEDIA_ROOT", "media"))
            out_dir = media_root / "import_errors"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            out_file = out_dir / f"assignments_import_errors_{ts}.csv"
            out_file.write_text(result.get("errors_csv", ""), encoding="utf-8")
            errors_path = (
                f"{settings.MEDIA_URL.rstrip('/')}/import_errors/{out_file.name}"
            )

        payload = {
            "created": result.get("created"),
            "updated": result.get("updated"),
            "errors": result.get("errors"),
            "total_rows": result.get("total_rows"),
            "dry_run": dry_run,
            "errors_csv_url": errors_path,
            "error_rows": result.get("error_rows", []),
        }
        return Response(payload, status=status.HTTP_200_OK)


@extend_schema(tags=["Assignments"])
class AssignmentsCSVLatestView(APIView):
    """
    GET /api/assignments/latest.csv
    Serves the most recent nightly export from ASSIGNMENTS_EXPORT_DIR.
    PM only (contains full mapping).
    """

    permission_classes = [IsAuthenticatedJWT & IsPropertyManager]

    def get(self, request):
        base = Path(getattr(settings, "ASSIGNMENTS_EXPORT_DIR", "exports"))
        base.mkdir(parents=True, exist_ok=True)
        # Pick newest by modified time or filename pattern
        candidates = sorted(
            base.glob("assignments_*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return Response({"detail": "No exports found yet."}, status=404)
        latest = candidates[0]
        return FileResponse(
            open(latest, "rb"),
            as_attachment=True,
            filename=latest.name,
            content_type="text/csv; charset=utf-8",
        )
