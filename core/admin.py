from django.contrib import admin
from .models import Condo, Unit, ParkingSpot, UnitParkingAssignment, ShortTermBooking


@admin.register(Condo)
class CondoAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "province", "code", "created_at")
    search_fields = ("name", "city", "code")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("unit_number", "condo", "owner_name", "owner_email", "status", "created_at")
    list_filter = ("condo", "status")
    search_fields = ("unit_number", "owner_name", "owner_email")
    autocomplete_fields = ("condo",)


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ("code", "condo", "level", "spot_type", "created_at")
    list_filter = ("condo", "spot_type", "level")
    search_fields = ("code",)
    autocomplete_fields = ("condo",)


@admin.register(UnitParkingAssignment)
class UnitParkingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("unit", "parking_spot", "start_date", "end_date", "is_primary", "created_at")
    list_filter = ("unit__condo", "is_primary")
    search_fields = ("unit__unit_number", "parking_spot__code")
    autocomplete_fields = ("unit", "parking_spot")


@admin.register(ShortTermBooking)
class ShortTermBookingAdmin(admin.ModelAdmin):
    list_display = ("unit", "guest_last_name", "check_in", "check_out", "status", "parking_spot", "created_at")
    list_filter = ("unit__condo", "status", "id_type")
    search_fields = ("guest_first_name", "guest_last_name", "id_number", "vehicle_plate", "unit__unit_number")
    autocomplete_fields = ("unit", "parking_spot")
