# core/middleware_audit.py
import json
from datetime import datetime

from django.conf import settings
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin


class AuditWriteMiddleware(MiddlewareMixin):
    """
    VERY simple file-based audit for POST/PUT/PATCH/DELETE.
    Writes newline-delimited JSON to MEDIA_ROOT/audit/audit.log
    (Swap to a DB model later if needed.)
    """

    def process_response(self, request: HttpRequest, response):
        if request.method in (
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        ) and request.path.startswith("/api/"):
            try:
                body = request.body.decode("utf-8")[:4096]
            except Exception:
                body = "<unreadable>"
            line = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
                "user": getattr(getattr(request, "user", None), "username", None),
                "ip": request.META.get("REMOTE_ADDR"),
                "body": body,
            }
            try:
                import os

                base = os.path.join(getattr(settings, "MEDIA_ROOT", "media"), "audit")
                os.makedirs(base, exist_ok=True)
                with open(os.path.join(base, "audit.log"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")
            except Exception:
                pass
        return response
