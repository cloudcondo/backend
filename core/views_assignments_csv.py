from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.csv_assignments import (
    export_assignments_to_csv,
    import_assignments_from_csv,
)


class AssignmentsCSVExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filename, content = export_assignments_to_csv()
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class AssignmentsCSVImportView(APIView):
    """
    POST multipart/form-data with 'file'.
    Optional query: ?dry_run=1
    Returns JSON summary and, if errors, a link to an error CSV file when not dry_run.
    """

    permission_classes = [IsAuthenticated]

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
        result = import_assignments_from_csv(file, dry_run=dry_run)

        errors_path = ""
        if result.get("errors") and not dry_run:
            # write error csv to MEDIA_ROOT/import_errors
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
            "error_rows": result.get("error_rows", []),  # keep details for UI too
        }
        return Response(payload, status=status.HTTP_200_OK)
