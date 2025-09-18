from django.apps import apps
from django.test import TestCase


class SmokeTest(TestCase):
    def test_core_app_loaded(self):
        self.assertTrue(apps.is_installed("core"))
