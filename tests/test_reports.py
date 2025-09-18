# core/tests/test_reports.py
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Unit


class ReportsTests(TestCase):
    fixtures = ["sample_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="t", password="t")
        self.client = APIClient()
        # JWT not required for test; we can force authenticate
        self.client.force_authenticate(user=self.user)

    def test_unit_bookings(self):
        unit = Unit.objects.first()
        resp = self.client.get(f"/api/reports/unit/{unit.id}/bookings")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())

    def test_available_spots(self):
        resp = self.client.get(
            "/api/reports/available-spots", {"date": "2025-09-16", "condo_id": 1}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())

    def test_upcoming(self):
        resp = self.client.get("/api/reports/upcoming-checkpoints", {"window": "7d"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())
