# core/tests/test_smoke.py
from django.test import TestCase
from rest_framework.test import APIClient


class SmokeTests(TestCase):
    def test_healthz(self):
        c = APIClient()
        r = c.get("/api/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True})
