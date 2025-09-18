from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path

# API schema / docs
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# JWT auth
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def home(_request):
    return HttpResponse("Condo backend is running")


def ping(_request):
    return JsonResponse({"pong": True})


def health(_request):
    return JsonResponse({"ok": True})


urlpatterns = [
    path("", home),
    path("api/healthz", health),
    path("api/ping", ping),
    # Core API (viewsets + CSV + reports)
    path("api/", include("core.urls")),
    # Auth (JWT)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # OpenAPI / Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def api_error(request, *args, **kwargs):
    return JsonResponse(
        {
            "error": {
                "code": "not_found",
                "detail": "The requested resource was not found.",
            }
        },
        status=404,
    )


handler404 = "condo_backend.urls.api_error"
