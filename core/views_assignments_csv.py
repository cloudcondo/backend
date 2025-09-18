# core/views_assignments_csv.py
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedJWT, IsPropertyManager

from .services.csv_assignments import (
    export_assignments_to_csv,
    import_assignments_from_csv,
)


class AssignmentsCSVExportView(APIView):
    permission_classes = [IsAuthenticatedJWT & IsPropertyManager]

    def get(self, request, *args, **kwargs):
        """
        Returns the current canonical assignments CSV as a file download.
        export_assignments_to_csv() must return (filename: str, content_bytes: bytes).
        """
        filename, content = export_assignments_to_csv()
        resp = HttpResponse(content, content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


class AssignmentsCSVImportView(APIView):
    permission_classes = [IsAuthenticatedJWT & IsPropertyManager]

    def post(self, request, *args, **kwargs):
        """
        Expect multipart/form-data with a 'file' field (CSV).
        """
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"detail": "Missing 'file'."}, status=status.HTTP_400_BAD_REQUEST
            )

        result = import_assignments_from_csv(csv_file)
        return Response(result, status=status.HTTP_200_OK)
