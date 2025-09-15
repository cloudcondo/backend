from rest_framework import viewsets, permissions
from .models import Condo, Unit, ParkingSpot, UnitParkingAssignment, ShortTermBooking
from .serializers import (
    CondoSerializer, UnitSerializer, ParkingSpotSerializer,
    UnitParkingAssignmentSerializer, ShortTermBookingSerializer
)

class CondoViewSet(viewsets.ModelViewSet):
    queryset = Condo.objects.all()
    serializer_class = CondoSerializer
    permission_classes = [permissions.AllowAny]  # tighten later

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.select_related("condo").all()
    serializer_class = UnitSerializer
    permission_classes = [permissions.AllowAny]

class ParkingSpotViewSet(viewsets.ModelViewSet):
    queryset = ParkingSpot.objects.select_related("condo").all()
    serializer_class = ParkingSpotSerializer
    permission_classes = [permissions.AllowAny]

class UnitParkingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = UnitParkingAssignment.objects.select_related("unit", "parking_spot").all()
    serializer_class = UnitParkingAssignmentSerializer
    permission_classes = [permissions.AllowAny]

class ShortTermBookingViewSet(viewsets.ModelViewSet):
    queryset = ShortTermBooking.objects.select_related("unit", "parking_spot").all()
    serializer_class = ShortTermBookingSerializer
    permission_classes = [permissions.AllowAny]
