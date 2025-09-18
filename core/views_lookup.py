from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ParkingSpot, Unit, UnitParkingAssignment


class UnitParkingLookupView(APIView):
    """
    GET /api/units/<unit_id>/parking
    Returns current and historical assignments for a unit.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, unit_id: int):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return Response(
                {"detail": "Unit not found."}, status=status.HTTP_404_NOT_FOUND
            )

        qs = (
            UnitParkingAssignment.objects.select_related("parking_spot", "unit__condo")
            .filter(unit=unit)
            .order_by("-start_date", "-id")
        )
        results = []
        for a in qs:
            results.append(
                {
                    "assignment_id": a.id,
                    "unit": str(a.unit),
                    "spot_id": a.parking_spot_id,
                    "spot_code": a.parking_spot.code if a.parking_spot_id else None,
                    "condo": a.unit.condo.code,
                    "start_date": a.start_date.isoformat() if a.start_date else None,
                    "end_date": a.end_date.isoformat() if a.end_date else None,
                    "is_active": a.end_date is None,
                    "is_primary": a.is_primary,
                }
            )
        return Response({"unit": str(unit), "count": len(results), "results": results})


class SpotUnitLookupView(APIView):
    """
    GET /api/spots/<spot_id>/unit
    Returns the current assigned unit (if any) and history for a spot.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, spot_id: int):
        try:
            spot = ParkingSpot.objects.get(pk=spot_id)
        except ParkingSpot.DoesNotExist:
            return Response(
                {"detail": "Parking spot not found."}, status=status.HTTP_404_NOT_FOUND
            )

        qs = (
            UnitParkingAssignment.objects.select_related("unit", "unit__condo")
            .filter(parking_spot=spot)
            .order_by("-start_date", "-id")
        )
        history = []
        current_unit = None
        for a in qs:
            item = {
                "assignment_id": a.id,
                "unit_id": a.unit_id,
                "unit": str(a.unit),
                "condo": a.unit.condo.code,
                "start_date": a.start_date.isoformat() if a.start_date else None,
                "end_date": a.end_date.isoformat() if a.end_date else None,
                "is_active": a.end_date is None,
                "is_primary": a.is_primary,
            }
            history.append(item)
            if a.end_date is None and current_unit is None:
                current_unit = {"unit_id": a.unit_id, "unit": str(a.unit)}

        return Response(
            {
                "spot": f"{spot.condo.code}-{spot.code}",
                "current_unit": current_unit,
                "history_count": len(history),
                "history": history,
            }
        )
