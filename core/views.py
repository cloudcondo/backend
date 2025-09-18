# core/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role, UnitAccess
from accounts.permissions import (
    IsAuthenticatedJWT,
    IsConcierge,
    IsPropertyManager,
    ReadOnly,
)

from .filters import ShortTermBookingFilter
from .models import Condo, ParkingSpot, ShortTermBooking, Unit, UnitParkingAssignment
from .serializers import (
    CondoSerializer,
    ParkingSpotSerializer,
    ShortTermBookingSerializer,
    UnitParkingAssignmentSerializer,
    UnitSerializer,
)


# ----- helpers -----
def user_units_qs(user):
    """Units this user can access (PM: all; others via UnitAccess)."""
    if not user.is_authenticated:
        return Unit.objects.none()
    role = getattr(getattr(user, "profile", None), "role", None)
    if role == Role.PROPERTY_MANAGER:
        return Unit.objects.all()
    unit_ids = UnitAccess.objects.filter(user=user).values_list("unit_id", flat=True)
    return Unit.objects.filter(id__in=unit_ids)


# ----- viewsets -----
class CondoViewSet(viewsets.ModelViewSet):
    queryset = Condo.objects.all()
    serializer_class = CondoSerializer
    permission_classes = [IsAuthenticatedJWT & (IsPropertyManager | ReadOnly)]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["code", "city", "province"]
    ordering = ["code"]


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticatedJWT & (IsPropertyManager | ReadOnly)]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["condo", "status", "unit_number"]
    ordering = ["unit_number"]

    def get_queryset(self):
        return user_units_qs(self.request.user).select_related("condo")


class ParkingSpotViewSet(viewsets.ModelViewSet):
    queryset = ParkingSpot.objects.select_related("condo").all()
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticatedJWT & (IsPropertyManager | ReadOnly)]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["condo", "spot_type", "level", "code"]
    ordering = ["code"]


class UnitParkingAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = UnitParkingAssignmentSerializer
    permission_classes = [IsAuthenticatedJWT & (IsPropertyManager | ReadOnly)]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["unit", "parking_spot", "is_primary", "unit__unit_number"]
    ordering = ["-start_date", "-created_at"]

    def get_queryset(self):
        units = user_units_qs(self.request.user)
        return UnitParkingAssignment.objects.select_related(
            "unit", "parking_spot"
        ).filter(unit__in=units)


class ShortTermBookingViewSet(viewsets.ModelViewSet):
    serializer_class = ShortTermBookingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ShortTermBookingFilter
    ordering = ["-check_in", "-created_at"]

    def get_permissions(self):
        """
        - PM: full access (list/create/update/delete + approve/reject).
        - Concierge: list/retrieve/update status (approve/reject). Cannot create/destroy.
        - Agent/Owner (via UnitAccess): can create & read their own bookings only.
        """
        role = getattr(getattr(self.request.user, "profile", None), "role", None)
        if role == Role.PROPERTY_MANAGER:
            return [IsAuthenticatedJWT()]
        if role == Role.CONCIERGE:
            if self.action in [
                "list",
                "retrieve",
                "update",
                "partial_update",
                "approve",
                "reject",
            ]:
                return [IsAuthenticatedJWT()]
            return [IsAuthenticatedJWT(), ReadOnly()]
        # agents/owners
        if self.action in ["create", "list", "retrieve"]:
            return [IsAuthenticatedJWT()]
        return [IsAuthenticatedJWT(), ReadOnly()]

    def get_queryset(self):
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", None)
        qs = ShortTermBooking.objects.select_related(
            "unit", "parking_spot", "submitted_by", "reviewed_by"
        )
        if role in [Role.PROPERTY_MANAGER, Role.CONCIERGE]:
            return qs
        units = user_units_qs(user)
        return qs.filter(unit__in=units)

    def perform_create(self, serializer):
        # agents/owners can only submit for units they have access to
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", None)
        if role not in [Role.PROPERTY_MANAGER, Role.CONCIERGE]:
            unit = serializer.validated_data.get("unit")
            if unit not in list(user_units_qs(user)):
                raise permissions.PermissionDenied("No access to selected unit.")
        serializer.save()

    @action(detail=True, methods=["POST"])
    def approve(self, request, pk=None):
        booking = self.get_object()
        role = getattr(getattr(request.user, "profile", None), "role", None)
        if role not in [Role.PROPERTY_MANAGER, Role.CONCIERGE]:
            return Response(
                {"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN
            )
        booking.status = "approved"
        booking.reviewed_by = request.user
        from django.utils import timezone

        booking.reviewed_at = timezone.now()
        booking.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response(
            ShortTermBookingSerializer(booking, context={"request": request}).data
        )

    @action(detail=True, methods=["POST"])
    def reject(self, request, pk=None):
        booking = self.get_object()
        role = getattr(getattr(request.user, "profile", None), "role", None)
        if role not in [Role.PROPERTY_MANAGER, Role.CONCIERGE]:
            return Response(
                {"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN
            )
        booking.status = "rejected"
        booking.reviewed_by = request.user
        from django.utils import timezone

        booking.reviewed_at = timezone.now()
        booking.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response(
            ShortTermBookingSerializer(booking, context={"request": request}).data
        )
