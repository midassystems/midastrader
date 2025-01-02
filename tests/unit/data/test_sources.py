import unittest
from midas.data.sources import Vendors
from midas.data.adaptors.historical import HistoricalAdaptor


class TestVendors(unittest.TestCase):
    def test_from_str(self):
        vendor = "historical"

        # Test
        enum = Vendors.from_str(vendor)
        self.assertEqual(enum, Vendors.HISTORICAL)

    def test_from_str_invalid(self):
        vendor = "invalid"

        # Test
        with self.assertRaises(ValueError):
            Vendors.from_str(vendor)

    def test_adapter(self):
        # Test
        enum = Vendors.HISTORICAL
        adapter = enum.adapter()
        self.assertEqual(adapter, HistoricalAdaptor)


if __name__ == "__main__":
    unittest.main()
