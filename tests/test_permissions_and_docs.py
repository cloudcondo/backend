import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import UnitAccess, UserProfile
from core.models import Condo, ParkingSpot, Unit, UnitParkingAssignment


class BaseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        U = get_user_model()

        # Users + roles
        self.pm = U.objects.create_user(
            username="pm", password="x", email="pm@example.com", is_staff=True
        )
        UserProfile.objects.create(user=self.pm, role="pm")

        self.con = U.objects.create_user(
            username="con", password="x", email="con@example.com"
        )
        UserProfile.objects.create(user=self.con, role="con")

        self.agent = U.objects.create_user(
            username="agent", password="x", email="agent@example.com"
        )
        UserProfile.objects.create(user=self.agent, role="agent")

        self.owner = U.objects.create_user(
            username="owner", password="x", email="owner@example.com"
        )
        UserProfile.objects.create(user=self.owner, role="own")

        self.rando = U.objects.create_user(
            username="rando", password="x", email="rando@example.com"
        )
        UserProfile.objects.create(user=self.rando, role=None)

        # Data
        self.condo = Condo.objects.create(
            code="C1", name="Condo One", city="Toronto", province="ON"
        )
        self.unit1 = Unit.objects.create(
            condo=self.condo,
            unit_number="101",
            owner_name="Alice",
            owner_email="a@x",
            status="active",
        )
        self.unit2 = Unit.objects.create(
            condo=self.condo,
            unit_number="102",
            owner_name="Bob",
            owner_email="b@x",
            status="active",
        )

        self.spot1 = ParkingSpot.objects.create(
            condo=self.condo, code="S1", level="L1", spot_type="standard"
        )
        self.spot2 = ParkingSpot.objects.create(
            condo=self.condo, code="S2", level="L1", spot_type="standard"
        )

        # Owner + Agent only see unit1
        UnitAccess.objects.create(user=self.owner, unit=self.unit1)
        UnitAccess.objects.create(user=self.agent, unit=self.unit1)

        UnitParkingAssignment.objects.create(
            unit=self.unit1, parking_spot=self.spot1, is_primary=True
        )
        UnitParkingAssignment.objects.create(
            unit=self.unit2, parking_spot=self.spot2, is_primary=True
        )

    # ------- Auth required on core endpoints -------
    def test_units_requires_auth(self):
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, 401)

    # ------- PM full access; list all units -------
    def test_pm_can_list_all_units(self):
        self.client.force_authenticate(self.pm)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, 200)
        # should see both 101 and 102
        nums = [row["unit_number"] for row in resp.data["results"]]
        self.assertCountEqual(nums, ["101", "102"])

    # ------- Owner sees only own units (via UnitAccess) -------
    def test_owner_sees_only_own_units(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, 200)
        nums = [row["unit_number"] for row in resp.data["results"]]
        self.assertEqual(nums, ["101"])

    # ------- Agent sees only own units (via UnitAccess) -------
    def test_agent_sees_only_own_units(self):
        self.client.force_authenticate(self.agent)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, 200)
        nums = [row["unit_number"] for row in resp.data["results"]]
        self.assertEqual(nums, ["101"])

    # ------- Concierge read-only for most models (enforced by view perms) -------
    def test_concierge_list_units_ok(self):
        self.client.force_authenticate(self.con)
        resp = self.client.get("/api/units/")
        self.assertEqual(resp.status_code, 200)

    # ------- CSV export/import: PM only -------
    def test_csv_export_import_permissions(self):
        # export denied for concierge
        self.client.force_authenticate(self.con)
        resp = self.client.get("/api/assignments/export.csv")
        self.assertEqual(resp.status_code, 403)

        # export allowed for PM
        self.client.force_authenticate(self.pm)
        resp = self.client.get("/api/assignments/export.csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])

        # import denied for owner/agent/concierge
        for user in [self.owner, self.agent, self.con]:
            self.client.force_authenticate(user)
            resp = self.client.post(
                "/api/assignments/import.csv", data={}, format="multipart"
            )
            self.assertEqual(resp.status_code, 403)

        # import allowed for PM (send a minimal valid CSV from memory)
        self.client.force_authenticate(self.pm)
        mem = io.StringIO()
        w = csv.writer(mem)
        # Header assumed by your service:
        w.writerow(
            [
                "condo_code",
                "unit_number",
                "parking_code",
                "status",
                "effective_start",
                "effective_end",
            ]
        )
        w.writerow(["C1", "101", "S1", "active", "", ""])
        mem.seek(0)

        resp = self.client.post(
            "/api/assignments/import.csv",
            data={"file": io.BytesIO(mem.read().encode("utf-8"))},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("created", resp.data)
        self.assertIn("updated", resp.data)
        self.assertIn("errors", resp.data)

    # ------- Docs available anonymously (schema/docs) -------
    def test_openapi_schema_and_docs(self):
        resp = self.client.get("/api/schema/")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("/api/docs/")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("/api/redoc/")
        self.assertEqual(resp.status_code, 200)
