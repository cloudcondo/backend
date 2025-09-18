# core/urls.py (only add the last two lines shown)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CondoViewSet,
    ParkingSpotViewSet,
    ShortTermBookingViewSet,
    UnitParkingAssignmentViewSet,
    UnitViewSet,
)
from .views_assignments_csv import AssignmentsCSVExportView, AssignmentsCSVImportView

router = DefaultRouter()
router.register(r"condos", CondoViewSet, basename="condo")
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"parking-spots", ParkingSpotViewSet, basename="parkingspot")
router.register(
    r"unit-parking-assignments",
    UnitParkingAssignmentViewSet,
    basename="unitparkingassignment",
)
router.register(r"bookings", ShortTermBookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    path("assignments/export.csv", AssignmentsCSVExportView.as_view()),
    path("assignments/import.csv", AssignmentsCSVImportView.as_view()),
    path("reports/", include("core.urls_reports")),  # <-- add this line
]
