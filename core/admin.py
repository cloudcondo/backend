from django.contrib import admin
from django.utils import timezone

from .models import Condo, ParkingSpot, ShortTermBooking, Unit, UnitParkingAssignment


@admin.register(Condo)
class CondoAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    search_fields = ("code", "name")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("id", "unit_number", "condo")
    list_filter = ("condo",)
    search_fields = ("unit_number",)
    autocomplete_fields = ("condo",)


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "condo", "level", "spot_type")
    list_filter = ("condo", "spot_type", "level")
    search_fields = ("code",)
    autocomplete_fields = ("condo",)


@admin.action(description="Approve selected bookings")
def approve_bookings(modeladmin, request, queryset):
    queryset.update(
        status="approved", reviewed_by=request.user, reviewed_at=timezone.now()
    )


@admin.action(description="Reject selected bookings")
def reject_bookings(modeladmin, request, queryset):
    queryset.update(
        status="rejected", reviewed_by=request.user, reviewed_at=timezone.now()
    )


@admin.register(UnitParkingAssignment)
class UnitParkingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "unit",
        "parking_spot",
        "start_date",
        "end_date",
        "is_primary",
    )
    list_filter = ("unit__condo", "is_primary")
    search_fields = ("unit__unit_number", "parking_spot__code")
    autocomplete_fields = ("unit", "parking_spot")


@admin.register(ShortTermBooking)
class ShortTermBookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "unit",
        "parking_spot",
        "guest_first_name",
        "guest_last_name",
        "check_in",
        "check_out",
        "status",
    )
    list_filter = ("unit__condo", "status")
    search_fields = (
        "guest_first_name",
        "guest_last_name",
        "vehicle_plate",
        "unit__unit_number",
        "parking_spot__code",
    )
    autocomplete_fields = ("unit", "parking_spot")
    actions = [approve_bookings, reject_bookings]
