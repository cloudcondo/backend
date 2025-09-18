# core/models.py
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Condo(TimeStampedModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)  # short identifier
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Unit(TimeStampedModel):
    class Status(models.TextChoices):
        OWNER_OCCUPIED = "OWNER_OCCUPIED", "Owner Occupied"
        TENANT = "TENANT", "Tenant"
        VACANT = "VACANT", "Vacant"

    condo = models.ForeignKey(Condo, on_delete=models.CASCADE, related_name="units")
    unit_number = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=200, blank=True)
    owner_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.OWNER_OCCUPIED
    )

    class Meta:
        unique_together = ("condo", "unit_number")

    def __str__(self) -> str:
        return f"{self.condo.code}-{self.unit_number}"


class ParkingSpot(TimeStampedModel):
    class SpotType(models.TextChoices):
        RESIDENT = "RESIDENT", "Resident"
        VISITOR = "VISITOR", "Visitor"

    condo = models.ForeignKey(
        Condo, on_delete=models.CASCADE, related_name="parking_spots"
    )
    code = models.CharField(max_length=50)  # e.g., P1-123
    level = models.CharField(max_length=50, blank=True)
    spot_type = models.CharField(
        max_length=16, choices=SpotType.choices, default=SpotType.RESIDENT
    )

    class Meta:
        unique_together = ("condo", "code")

    def __str__(self) -> str:
        return f"{self.condo.code}-{self.code}"


class UnitParkingAssignment(TimeStampedModel):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="parking_assignments"
    )
    parking_spot = models.ForeignKey(
        ParkingSpot, on_delete=models.CASCADE, related_name="assignments"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # open-ended
    is_primary = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.unit} → {self.parking_spot}"


class ShortTermBooking(TimeStampedModel):
    class IdType(models.TextChoices):
        LICENSE = "LICENSE", "Driver’s License"
        PASSPORT = "PASSPORT", "Passport"
        OTHER = "OTHER", "Other"

    # lower-case to match views (.approve/.reject) and serializer
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="bookings")

    # guest info
    guest_first_name = models.CharField(max_length=120)
    guest_last_name = models.CharField(max_length=120)
    id_type = models.CharField(
        max_length=16, choices=IdType.choices, default=IdType.LICENSE
    )
    id_number = models.CharField(max_length=120, blank=True)
    id_country = models.CharField(max_length=120, blank=True)
    id_province_state = models.CharField(max_length=120, blank=True)

    # vehicle & parking
    vehicle_plate = models.CharField(max_length=50, blank=True)
    parking_spot = models.ForeignKey(
        ParkingSpot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    # stay dates (date granularity is fine)
    check_in = models.DateField()
    check_out = models.DateField()

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField(blank=True)

    # RBAC workflow tracking (matches serializer)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_submitted",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # optional file upload for ID image/PDF
    id_document = models.FileField(upload_to="ids/", null=True, blank=True)

    class Meta:
        ordering = ["-check_in"]

    def __str__(self) -> str:
        return f"Booking {self.unit} {self.check_in}→{self.check_out} ({self.status})"
