# accounts/management/commands/seed_demo.py
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UnitAccess, UserProfile
from core.models import (
    Condo,
    ParkingSpot,
    ShortTermBooking,
    Unit,
    UnitParkingAssignment,
)


class Command(BaseCommand):
    help = "Seeds demo data: users with roles, units, parking, unit access, and a sample booking"

    @transaction.atomic
    def handle(self, *args, **options):
        U = get_user_model()

        # --- Users ---
        users = {
            "pm": {"username": "pm", "email": "pm@example.com", "password": "changeme"},
            "con": {
                "username": "con",
                "email": "con@example.com",
                "password": "changeme",
            },
            "agent": {
                "username": "agent",
                "email": "agent@example.com",
                "password": "changeme",
            },
            "owner": {
                "username": "owner",
                "email": "owner@example.com",
                "password": "changeme",
            },
        }
        created_users = {}
        for role_key, payload in users.items():
            user, created = U.objects.get_or_create(
                username=payload["username"], defaults={"email": payload["email"]}
            )
            if created:
                user.set_password(payload["password"])
                user.is_staff = role_key == "pm" or role_key == "con"
                user.is_superuser = False
                user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role_key  # 'pm', 'con', 'agent', 'own'
            if role_key == "owner":
                profile.role = "own"
            profile.save()
            created_users[role_key] = user

        # --- Condos / Units / Parking ---
        condo, _ = Condo.objects.get_or_create(
            code="CC01",
            defaults={"name": "Cloud Condo One", "city": "Toronto", "province": "ON"},
        )
        unit101, _ = Unit.objects.get_or_create(
            condo=condo,
            unit_number="101",
            defaults={
                "owner_name": "Alice Owner",
                "owner_email": "alice@example.com",
                "status": "active",
            },
        )
        unit102, _ = Unit.objects.get_or_create(
            condo=condo,
            unit_number="102",
            defaults={
                "owner_name": "Bob Owner",
                "owner_email": "bob@example.com",
                "status": "active",
            },
        )

        spotA1, _ = ParkingSpot.objects.get_or_create(
            condo=condo, code="A1", defaults={"level": "P1", "spot_type": "visitor"}
        )
        spotA2, _ = ParkingSpot.objects.get_or_create(
            condo=condo, code="A2", defaults={"level": "P1", "spot_type": "standard"}
        )

        UnitParkingAssignment.objects.get_or_create(
            unit=unit101, parking_spot=spotA2, defaults={"is_primary": True}
        )

        # --- UnitAccess (agent + owner can access unit 101) ---
        UnitAccess.objects.get_or_create(user=created_users["agent"], unit=unit101)
        UnitAccess.objects.get_or_create(user=created_users["owner"], unit=unit101)

        # --- Sample booking (pending) ---
        ShortTermBooking.objects.get_or_create(
            unit=unit101,
            parking_spot=spotA1,
            guest_first_name="Guest",
            guest_last_name="Example",
            defaults={
                "id_type": "passport",
                "id_number": "X1234567",
                "id_country": "CA",
                "vehicle_plate": "TEST-123",
                "check_in": "2025-09-20",
                "check_out": "2025-09-22",
                "status": "pending",
            },
        )

        self.stdout.write(self.style.SUCCESS("✅ Seeded demo data."))
        self.stdout.write(self.style.SUCCESS("Users (password for all = 'changeme'):"))
        self.stdout.write("  - pm      (Property Manager, staff)")
        self.stdout.write("  - con     (Concierge, staff)")
        self.stdout.write("  - agent   (3rd-party rental manager)")
        self.stdout.write("  - owner   (Unit owner)")
