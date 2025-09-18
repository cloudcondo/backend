# core/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Condo, ParkingSpot, ShortTermBooking, Unit, UnitParkingAssignment

User = get_user_model()


class CondoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condo
        fields = "__all__"


class UnitSerializer(serializers.ModelSerializer):
    condo_name = serializers.CharField(source="condo.name", read_only=True)

    class Meta:
        model = Unit
        fields = [
            "id",
            "condo",
            "condo_name",
            "unit_number",
            "owner_name",
            "owner_email",
            "status",
            "created_at",
            "updated_at",
        ]


class ParkingSpotSerializer(serializers.ModelSerializer):
    condo_name = serializers.CharField(source="condo.name", read_only=True)

    class Meta:
        model = ParkingSpot
        fields = [
            "id",
            "condo",
            "condo_name",
            "code",
            "level",
            "spot_type",
            "created_at",
            "updated_at",
        ]


class UnitParkingAssignmentSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source="unit.__str__", read_only=True)
    spot_display = serializers.CharField(source="parking_spot.__str__", read_only=True)

    class Meta:
        model = UnitParkingAssignment
        fields = [
            "id",
            "unit",
            "unit_display",
            "parking_spot",
            "spot_display",
            "start_date",
            "end_date",
            "is_primary",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        unit = attrs.get("unit") or getattr(self.instance, "unit", None)
        spot = attrs.get("parking_spot") or getattr(self.instance, "parking_spot", None)
        if unit and spot and unit.condo_id != spot.condo_id:
            raise serializers.ValidationError(
                "Unit and Parking Spot must belong to the same condo."
            )
        return attrs


class ShortTermBookingSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source="unit.__str__", read_only=True)
    spot_display = serializers.CharField(source="parking_spot.__str__", read_only=True)

    # RBAC workflow fields
    submitted_by_username = serializers.CharField(
        source="submitted_by.username", read_only=True
    )
    reviewed_by_username = serializers.CharField(
        source="reviewed_by.username", read_only=True
    )
    id_document = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = ShortTermBooking
        fields = [
            "id",
            "unit",
            "unit_display",
            "guest_first_name",
            "guest_last_name",
            "id_type",
            "id_number",
            "id_country",
            "id_province_state",
            "vehicle_plate",
            "parking_spot",
            "spot_display",
            "check_in",
            "check_out",
            "status",
            "notes",
            "id_document",
            "submitted_by",
            "submitted_by_username",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "submitted_by",
            "submitted_by_username",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        check_in = attrs.get("check_in") or getattr(self.instance, "check_in", None)
        check_out = attrs.get("check_out") or getattr(self.instance, "check_out", None)
        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError(
                "check_out must be the same day or after check_in."
            )

        unit = attrs.get("unit") or getattr(self.instance, "unit", None)
        spot = attrs.get("parking_spot") or getattr(self.instance, "parking_spot", None)
        if unit and spot and unit.condo_id != spot.condo_id:
            raise serializers.ValidationError(
                "Selected parking spot must belong to the same condo as the unit."
            )
        return attrs

    def create(self, validated_data):
        # record who submitted (owner/agent/concierge/pm)
        user = self.context["request"].user if "request" in self.context else None
        if user and user.is_authenticated:
            validated_data["submitted_by"] = user
        return super().create(validated_data)
