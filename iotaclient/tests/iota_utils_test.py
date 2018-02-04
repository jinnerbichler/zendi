from django.test import TestCase

from iotaclient.iota_.iota_utils import iota_display_format


class UtilsTestCase(TestCase):
    def test_display_format(self):
        """Tests proper front end format of IOTA amount"""

        self.assertEqual((500.0, 'i'), iota_display_format(500.0))
        self.assertEqual((1000.0, 'i'), iota_display_format(10 ** 3))
        self.assertEqual((10000.0, 'i'), iota_display_format(10 ** 4))

        self.assertEqual((100.0, 'Ki'), iota_display_format(10 ** 5))
        self.assertEqual((1000.0, 'Ki'), iota_display_format(10 ** 6))
        self.assertEqual((10000.0, 'Ki'), iota_display_format(10 ** 7))

        self.assertEqual((40.0, 'Mi'), iota_display_format(10 ** 7 * 4))
        self.assertEqual((400.0, 'Mi'), iota_display_format(10 ** 8 * 4))
        self.assertEqual((4000.0, 'Mi'), iota_display_format(10 ** 9 * 4))

        self.assertEqual((50.0, 'Gi'), iota_display_format(10 ** 10 * 5))
        self.assertEqual((550.0, 'Gi'), iota_display_format(10 ** 11 * 5.5))
        self.assertEqual((6600.0, 'Gi'), iota_display_format(10 ** 12 * 6.6))
