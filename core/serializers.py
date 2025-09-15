from rest_framework import serializers
from .models import Condo, Unit, ParkingSpot, UnitParkingAssignment, ShortTermBooking

class CondoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condo
        fields = ["id", "name", "address", "city", "province", "code", "created_at"]

class UnitSerializer(serializers.ModelSerializer):
    condo = serializers.PrimaryKeyRelatedField(queryset=Condo.objects.all())
    class Meta:
        model = Unit
        fields = ["id", "condo", "unit_number", "owner_name", "owner_email", "status", "created_at"]

class ParkingSpotSerializer(serializers.ModelSerializer):
    condo = serializers.PrimaryKeyRelatedField(queryset=Condo.objects.all())
    class Meta:
        model = ParkingSpot
        fields = ["id", "condo", "code", "level", "spot_type", "notes", "created_at"]

class UnitParkingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitParkingAssignment
        fields = ["id", "unit", "parking_spot", "start_date", "end_date", "is_primary", "created_at"]

    def validate(self, data):
        # basic cross-field date check
        start = data.get("start_date") or getattr(self.instance, "start_date", None)
        end = data.get("end_date") or getattr(self.instance, "end_date", None)
        if end and start and end < start:
            raise serializers.ValidationError("end_date cannot be before start_date.")
        return data

class ShortTermBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortTermBooking
        fields = [
            "id", "unit",
            "guest_first_name", "guest_last_name", "guest_email", "guest_phone",
            "id_type", "id_number", "id_country", "id_province_state", "id_city",
            "check_in", "check_out", "num_guests",
            "vehicle_plate", "parking_spot",
            "status", "created_by_email", "approved_by", "approved_at",
            "notes", "created_at",
        ]

    def validate(self, data):
        ci = data.get("check_in") or getattr(self.instance, "check_in", None)
        co = data.get("check_out") or getattr(self.instance, "check_out", None)
        if ci and co and co <= ci:
            raise serializers.ValidationError("check_out must be after check_in.")
        return data
