from django.test import TestCase
from django.apps import apps

class SmokeTest(TestCase):
    def test_core_app_loaded(self):
        self.assertTrue(apps.is_installed("core"))
