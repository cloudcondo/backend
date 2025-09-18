from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Role:
    """Lightweight enum-like constants used in views/permissions."""

    PROPERTY_MANAGER = "pm"
    CONCIERGE = "concierge"
    OWNER = "owner"
    GUEST = "guest"
    PARTNER = "partner"  # Rental manager / 3rd-party agent

    CHOICES = [
        (PROPERTY_MANAGER, "Property Manager"),
        (CONCIERGE, "Concierge"),
        (OWNER, "Owner"),
        (GUEST, "Guest"),
        (PARTNER, "Rental Manager / Partner"),
    ]


class AccessType:
    OWNER = "owner"
    RENTAL_MANAGER = "rental_manager"
    TENANT = "tenant"
    GUEST_SUBMITTER = "guest_submitter"

    CHOICES = [
        (OWNER, "Owner"),
        (RENTAL_MANAGER, "Rental Manager"),
        (TENANT, "Tenant"),
        (GUEST_SUBMITTER, "Guest Submitter"),
    ]


class UserProfile(models.Model):
    """
    Per-user role (highest/global role) and optional condo affinity.
    Use UnitAccess for per-unit permissions.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.CHOICES, default=Role.GUEST)
    condo = models.ForeignKey(
        "core.Condo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Primary condo this user is associated with (optional).",
    )
    phone = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_userprofile"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        return f"{self.user} · {self.get_role_display()}"


class UnitAccess(models.Model):
    """
    Grants a user access/authority for a specific Unit.
    Useful when the owner uses a third-party rental manager to submit guests.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="unit_accesses"
    )
    unit = models.ForeignKey(
        "core.Unit", on_delete=models.CASCADE, related_name="accesses"
    )
    access_type = models.CharField(
        max_length=20, choices=AccessType.CHOICES, default=AccessType.OWNER
    )
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_unitaccess"
        unique_together = [("user", "unit", "access_type")]
        verbose_name = "Unit Access"
        verbose_name_plural = "Unit Access"

    def __str__(self) -> str:
        return f"{self.user} ↔ {self.unit} ({self.get_access_type_display()})"
