from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from rest_framework.routers import DefaultRouter
from core.views import (
    CondoViewSet, UnitViewSet, ParkingSpotViewSet,
    UnitParkingAssignmentViewSet, ShortTermBookingViewSet
)

def home(_request):
    return HttpResponse("Condo backend is running")

def ping(_request):
    return JsonResponse({"pong": True})

def health(_request):                     # <— add this
    return JsonResponse({"ok": True})

router = DefaultRouter()
router.register(r"condos", CondoViewSet, basename="condo")
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"parking-spots", ParkingSpotViewSet, basename="parkingspot")
router.register(r"unit-parking-assignments", UnitParkingAssignmentViewSet, basename="unitparkingassignment")
router.register(r"bookings", ShortTermBookingViewSet, basename="booking")

urlpatterns = [
    path("", home),
    path("api/healthz", health),          # <— add this
    path("api/ping", ping),
    path("api/", include(router.urls)),
    path("admin/", admin.site.urls),
]
