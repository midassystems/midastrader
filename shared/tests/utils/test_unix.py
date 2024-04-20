import unittest
import pandas as pd
from unittest.mock import Mock, patch
from contextlib import ExitStack
from decimal import Decimal
from shared.utils.unix import iso_to_unix, unix_to_iso

class TestConvertToUnix(unittest.TestCase):
    def test_iso_to_unix_tz_aware(self):
        iso_timestamp = "2024-02-07T12:00:00+00:00" 
        
        # test
        unix_timestamp=iso_to_unix(iso_timestamp)

        # valdiate
        self.assertEqual(unix_timestamp,1707307200)


    def test_iso_to_unix_tz_naive(self):
        iso_timestamp = "2023-02-07T12:00:00" 
        
        # test
        unix_timestamp=iso_to_unix(iso_timestamp)

        # valdiate
        self.assertEqual(unix_timestamp,1675789200)

    def test_unix_to_ios_UTC(self):
        unix_timestamp =  1679789200
        
        # test
        iso_timestamp=unix_to_iso(unix_timestamp)

        # valdiate
        self.assertEqual(iso_timestamp,"2023-03-26T00:06:40+00:00")

    def test_unix_to_ios_EST(self):
        unix_timestamp =  1679789200
        
        # test
        iso_timestamp=unix_to_iso(unix_timestamp, "US/Eastern")

        # valdiate
        self.assertEqual(iso_timestamp,"2023-03-25T20:06:40-04:00")


if __name__ =="__main__":
    unittest.main()