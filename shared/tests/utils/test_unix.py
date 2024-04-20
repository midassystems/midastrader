import unittest
import pandas as pd
from unittest.mock import Mock, patch
from contextlib import ExitStack
from decimal import Decimal
from shared.utils.unix import convert_to_unix

class TestConvertToUnix(unittest.TestCase):
    def test_date_format_1(self):
        timestamp_1="2024-01-10T12:00:00"
        # test
        unix_1=convert_to_unix(timestamp_1)

        # valdiate
        self.assertEqual(unix_1,1704888000)

    def test_date_format_2(self):
        timestamp_2="2023-01-10 12:00:00"
        # test
        unix_2=convert_to_unix(timestamp_2)

        # valdiate
        self.assertEqual(unix_2,1673352000)

if __name__ =="__main__":
    unittest.main()