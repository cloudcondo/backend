from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Condo, ParkingSpot, Unit, UnitParkingAssignment


class CsvDryRunAndLookupTests(TestCase):
    fixtures = ["sample_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="t", password="t")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_unit_parking_lookup(self):
        unit = Unit.objects.first()
        resp = self.client.get(f"/api/units/{unit.id}/parking")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())

    def test_spot_unit_lookup(self):
        spot = ParkingSpot.objects.first()
        resp = self.client.get(f"/api/spots/{spot.id}/unit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("history", resp.json())

    def test_csv_import_dry_run(self):
        condo = Condo.objects.first()
        unit = Unit.objects.filter(condo=condo).first()
        spot = ParkingSpot.objects.filter(condo=condo).first()
        csv_text = (
            "condo_code,unit_number,parking_code,start_date,end_date,is_primary\n"
            f"{condo.code},{unit.unit_number},{spot.code},2025-01-01,,true\n"
        )
        upload = SimpleUploadedFile(
            "dry_run.csv", csv_text.encode("utf-8"), content_type="text/csv"
        )
        resp = self.client.post(
            "/api/assignments/import.csv?dry_run=1",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["dry_run"])
        # Ensure DB not changed
        self.assertFalse(
            UnitParkingAssignment.objects.filter(
                unit=unit, parking_spot=spot, is_primary=True
            ).exists()
        )
        self.assertIn("total_rows", data)
