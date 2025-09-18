# tests/test_lookup_permissions.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UnitAccess, UserProfile
from core.models import Condo, ParkingSpot, Unit, UnitParkingAssignment


class LookupPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.condo = Condo.objects.create(code="CC02", name="Cloud Condo Two")
        cls.unit = Unit.objects.create(condo=cls.condo, unit_number="201")
        cls.other_unit = Unit.objects.create(condo=cls.condo, unit_number="202")
        cls.spot = ParkingSpot.objects.create(condo=cls.condo, code="B1")
        UnitParkingAssignment.objects.create(
            unit=cls.unit, parking_spot=cls.spot, is_primary=True
        )

        U = get_user_model()
        cls.pm = U.objects.create_user(username="pm2", password="x", is_staff=True)
        UserProfile.objects.create(user=cls.pm, role="pm")

        cls.con = U.objects.create_user(username="con2", password="x", is_staff=True)
        UserProfile.objects.create(user=cls.con, role="con")

        cls.owner = U.objects.create_user(username="own2", password="x")
        UserProfile.objects.create(user=cls.owner, role="own")
        UnitAccess.objects.create(user=cls.owner, unit=cls.unit)

        cls.agent = U.objects.create_user(username="agent2", password="x")
        UserProfile.objects.create(user=cls.agent, role="agent")
        # agent has no access rows

    def test_unauth_blocked(self):
        c = APIClient()
        self.assertEqual(c.get(f"/api/units/{self.unit.id}/parking").status_code, 401)
        self.assertEqual(c.get(f"/api/spots/{self.spot.id}/unit").status_code, 401)

    def test_pm_allowed(self):
        c = APIClient()
        c.force_authenticate(self.pm)
        self.assertEqual(c.get(f"/api/units/{self.unit.id}/parking").status_code, 200)
        self.assertEqual(c.get(f"/api/spots/{self.spot.id}/unit").status_code, 200)

    def test_concierge_allowed(self):
        c = APIClient()
        c.force_authenticate(self.con)
        self.assertEqual(c.get(f"/api/units/{self.unit.id}/parking").status_code, 200)
        self.assertEqual(c.get(f"/api/spots/{self.spot.id}/unit").status_code, 200)

    def test_owner_with_access_allowed(self):
        c = APIClient()
        c.force_authenticate(self.owner)
        self.assertEqual(c.get(f"/api/units/{self.unit.id}/parking").status_code, 200)
        self.assertEqual(c.get(f"/api/spots/{self.spot.id}/unit").status_code, 200)

    def test_agent_without_access_denied(self):
        c = APIClient()
        c.force_authenticate(self.agent)
        # no UnitAccess -> should be 403
        self.assertEqual(c.get(f"/api/units/{self.unit.id}/parking").status_code, 403)
        self.assertEqual(c.get(f"/api/spots/{self.spot.id}/unit").status_code, 403)

    def test_owner_denied_for_other_unit(self):
        c = APIClient()
        c.force_authenticate(self.owner)
        # owner has access only to self.unit
        self.assertEqual(
            c.get(f"/api/units/{self.other_unit.id}/parking").status_code, 403
        )
