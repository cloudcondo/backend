# core/urls_reports.py
from django.urls import path

from .views_reports import (
    AvailableSpotsReportView,
    UnitBookingsReportView,
    UpcomingCheckpointsReportView,
)

urlpatterns = [
    path("unit/<int:unit_id>/bookings", UnitBookingsReportView.as_view()),
    path("available-spots", AvailableSpotsReportView.as_view()),
    path("upcoming-checkpoints", UpcomingCheckpointsReportView.as_view()),
]
