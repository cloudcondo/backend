from django.test import TestCase

from core.models import (
    Condo,
    ParkingSpot,
    ShortTermBooking,
    Unit,
    UnitParkingAssignment,
)


class FixtureSmokeTests(TestCase):
    fixtures = ["sample_data.json"]

    def test_counts_and_linkage(self):
        self.assertEqual(Condo.objects.count(), 1)
        self.assertEqual(Unit.objects.count(), 2)
        self.assertEqual(ParkingSpot.objects.count(), 2)
        self.assertEqual(UnitParkingAssignment.objects.count(), 2)
        # linkage: confirm each unit has a spot via assignment
        a1 = UnitParkingAssignment.objects.get(unit__unit_number="905")
        self.assertIsNotNone(a1.parking_spot_id)
        # bookings fixture present
        self.assertEqual(ShortTermBooking.objects.count(), 1)
