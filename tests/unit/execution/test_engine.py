import unittest
from midas.execution.engine import Executors
from midas.execution.adaptors import IBAdaptor


class TestVendors(unittest.TestCase):
    def test_from_str(self):
        executor = "interactive_brokers"

        # Test
        enum = Executors.from_str(executor)
        self.assertEqual(enum, Executors.IB)

    def test_from_str_invalid(self):
        vendor = "invalid"

        # Test
        with self.assertRaises(ValueError):
            Executors.from_str(vendor)

    def test_adapter(self):
        # Test
        enum = Executors.IB
        adapter = enum.adapter()
        self.assertEqual(adapter, IBAdaptor)


if __name__ == "__main__":
    unittest.main()
