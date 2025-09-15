from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# ---------- Core ----------

class Condo(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=50, blank=True)  # e.g., ON
    code = models.CharField(max_length=50, blank=True)      # internal code if you use one
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Unit(models.Model):
    condo = models.ForeignKey(Condo, on_delete=models.CASCADE, related_name="units")
    unit_number = models.CharField(max_length=20)  # e.g., 201, PH01
    owner_name = models.CharField(max_length=200, blank=True)
    owner_email = models.EmailField(blank=True)
    status = models.CharField(max_length=30, blank=True)  # e.g., owner-occupied, tenanted
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("condo", "unit_number")
        ordering = ["condo__name", "unit_number"]

    def __str__(self):
        return f"{self.condo.name} - {self.unit_number}"


# ---------- Parking ----------

class ParkingSpot(models.Model):
    condo = models.ForeignKey(Condo, on_delete=models.CASCADE, related_name="parking_spots")
    code = models.CharField(max_length=50)                 # e.g., P1-123
    level = models.CharField(max_length=50, blank=True)    # e.g., P1
    spot_type = models.CharField(max_length=30, blank=True)  # e.g., assigned, visitor
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("condo", "code")
        ordering = ["condo__name", "code"]

    def __str__(self):
        return f"{self.condo.name} - {self.code}"


class UnitParkingAssignment(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="parking_assignments")
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.PROTECT, related_name="assignments")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)     # null = open-ended
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["unit__condo__name", "unit__unit_number", "-start_date"]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be before start_date.")
        if self.parking_spot.condo_id != self.unit.condo_id:
            raise ValidationError("Parking spot must belong to the same condo as the unit.")

    def __str__(self):
        return f"{self.unit} -> {self.parking_spot} ({self.start_date} → {self.end_date or 'open'})"


# ---------- Short-Term Rental Booking ----------

ID_TYPE_CHOICES = [
    ("DL", "Driver License"),
    ("PASS", "Passport"),
    ("NID", "National ID"),
    ("OTHER", "Other"),
]

BOOKING_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
    ("completed", "Completed"),
]

class ShortTermBooking(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="str_bookings")

    # Guest info
    guest_first_name = models.CharField(max_length=100)
    guest_last_name = models.CharField(max_length=100)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=50, blank=True)

    # Government ID
    id_type = models.CharField(max_length=10, choices=ID_TYPE_CHOICES, default="DL")
    id_number = models.CharField(max_length=100)
    id_country = models.CharField(max_length=100, blank=True)
    id_province_state = models.CharField(max_length=100, blank=True)
    id_city = models.CharField(max_length=100, blank=True)

    # Stay details
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    num_guests = models.PositiveIntegerField(default=1)

    # Vehicle and parking (optional)
    vehicle_plate = models.CharField(max_length=30, blank=True)
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, blank=True, null=True)

    # Workflow
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default="pending")
    created_by_email = models.EmailField(blank=True)   # owner/host email who submitted
    approved_by = models.CharField(max_length=150, blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-check_in"]

    def clean(self):
        if self.check_out <= self.check_in:
            raise ValidationError("check_out must be after check_in.")
        if self.parking_spot and self.parking_spot.condo_id != self.unit.condo_id:
            raise ValidationError("Selected parking spot is not in the same condo as the unit.")

    @property
    def is_active_now(self):
        now = timezone.now()
        return self.status in {"approved", "completed"} and self.check_in <= now <= self.check_out

    def __str__(self):
        return f"{self.unit} | {self.guest_first_name} {self.guest_last_name} | {self.check_in:%Y-%m-%d} → {self.check_out:%Y-%m-%d}"
