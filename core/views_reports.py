# core/views_reports.py
from datetime import date, timedelta

from django.db.models import Q
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedJWT

from .models import ParkingSpot, ShortTermBooking, Unit, UnitParkingAssignment


def _parse_window(window_param: str) -> timedelta:
    if not window_param:
        return timedelta(days=7)
    try:
        if window_param.endswith("d"):
            return timedelta(days=int(window_param[:-1]))
        return timedelta(days=int(window_param))
    except Exception:
        return timedelta(days=7)


@extend_schema(tags=["Reports"])
class UnitBookingsReportView(APIView):
    """
    GET /reports/unit/{id}/bookings
    Returns bookings for a unit (past + upcoming, newest first).
    Query params:
      - status (optional): pending|approved|rejected|cancelled
    """

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, unit_id: int, *args, **kwargs):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return Response(
                {"detail": "Unit not found."}, status=status.HTTP_404_NOT_FOUND
            )

        qs = (
            ShortTermBooking.objects.select_related("unit", "parking_spot")
            .filter(unit=unit)
            .order_by("-check_in", "-created_at")
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        data = [
            {
                "id": b.id,
                "unit": str(b.unit),
                "parking_spot": str(b.parking_spot) if b.parking_spot_id else None,
                "guest_first_name": b.guest_first_name,
                "guest_last_name": b.guest_last_name,
                "vehicle_plate": b.vehicle_plate,
                "check_in": b.check_in.isoformat(),
                "check_out": b.check_out.isoformat(),
                "status": b.status,
                "notes": b.notes,
            }
            for b in qs
        ]
        return Response({"unit": str(unit), "count": len(data), "results": data})


@extend_schema(tags=["Reports"])
class AvailableSpotsReportView(APIView):
    """
    GET /reports/available-spots?date=YYYY-MM-DD&condo_id=<id>
    Lists resident spots in a condo that are NOT assigned on that date and NOT booked for that date.
    """

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, *args, **kwargs):
        d_str = request.query_params.get("date")
        condo_id = request.query_params.get("condo_id")
        d = parse_date(d_str) if d_str else date.today()
        if not d:
            return Response(
                {"detail": "Invalid date."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not condo_id:
            return Response(
                {"detail": "Missing condo_id."}, status=status.HTTP_400_BAD_REQUEST
            )

        spots = ParkingSpot.objects.filter(condo_id=condo_id)

        active_assignments = UnitParkingAssignment.objects.filter(
            parking_spot__in=spots,
            start_date__lte=d,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=d))
        assigned_spot_ids = set(
            active_assignments.values_list("parking_spot_id", flat=True)
        )

        day_q = Q(check_in__lte=d, check_out__gte=d)
        day_booked_spot_ids = set(
            ShortTermBooking.objects.filter(parking_spot__in=spots)
            .filter(day_q)
            .values_list("parking_spot_id", flat=True)
        )

        unavailable = assigned_spot_ids.union(day_booked_spot_ids)
        available = spots.exclude(id__in=unavailable).order_by("code")

        results = [
            {"id": s.id, "spot": str(s), "code": s.code, "level": s.level}
            for s in available
        ]
        return Response(
            {
                "date": d.isoformat(),
                "condo_id": int(condo_id),
                "count": len(results),
                "results": results,
            }
        )


@extend_schema(tags=["Reports"])
class UpcomingCheckpointsReportView(APIView):
    """
    GET /reports/upcoming-checkpoints?window=7d
    Returns bookings starting within the next 'window' days.
    """

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, *args, **kwargs):
        window = _parse_window(request.query_params.get("window"))
        today = date.today()
        end = today + window
        qs = (
            ShortTermBooking.objects.select_related("unit", "parking_spot")
            .filter(check_in__gte=today, check_in__lte=end)
            .order_by("check_in", "unit__unit_number")
        )
        data = [
            {
                "id": b.id,
                "check_in": b.check_in.isoformat(),
                "check_out": b.check_out.isoformat(),
                "unit": str(b.unit),
                "parking_spot": str(b.parking_spot) if b.parking_spot_id else None,
                "guest": f"{b.guest_first_name} {b.guest_last_name}",
                "status": b.status,
            }
            for b in qs
        ]
        return Response(
            {"window_days": window.days, "count": len(data), "results": data}
        )
