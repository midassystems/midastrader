import unittest
import pandas as pd
import numpy as np

from midas.shared.utils.unix import iso_to_unix, unix_to_iso, resample_daily

class TestConvertToUnix(unittest.TestCase):
    def setUp(self) -> None:
        # MOck UNIX timestamps incremented by hours
        timestamp_range = [ 1714658400000000000, 1714662000000000000, 1714665600000000000,
                            1714669200000000000, 1714672800000000000, 1714741200000000000,
                            1714744800000000000]
        
        # Mock data
        col = [1,2,3,4,5,6,7]

        # Create DataFrame
        self.mock_df = pd.DataFrame({
            'UNIX_Timestamp': timestamp_range,
            'Col1': col,
        })
        self.mock_df.set_index('UNIX_Timestamp', inplace=True)
    
    # Basic Validation
    def test_iso_to_unix_tz_aware(self):
        iso_timestamp = "2024-02-07T12:00:00+00:00" 
        
        # Test
        unix_timestamp=iso_to_unix(iso_timestamp)

        # Valdiate
        self.assertEqual(unix_timestamp, 1707307200000000000)

    def test_iso_to_unix_tz_naive(self):
        iso_timestamp = "2023-02-07T12:00:00" 
        
        # Test
        unix_timestamp=iso_to_unix(iso_timestamp)

        # Valdiate
        self.assertEqual(unix_timestamp,1675789200000000000)

    def test_unix_to_ios_UTC(self):
        unix_timestamp =  1679789200000000000
        
        # Test
        iso_timestamp=unix_to_iso(unix_timestamp)

        # Valdiate
        self.assertEqual(iso_timestamp,"2023-03-26T00:06:40+00:00")

    def test_unix_to_ios_EST(self):
        unix_timestamp =  1679789200000000000
        
        # Test
        iso_timestamp=unix_to_iso(unix_timestamp, "US/Eastern")

        # Valdiate
        self.assertEqual(iso_timestamp,"2023-03-25T20:06:40-04:00")

    def test_resample_daily_UTC(self):
        # Test
        actual_df = resample_daily(self.mock_df)

        # Expected
        UNIX_Timestamp =[1714672800000000000, 1714744800000000000]
        col= [5,7]

        expected_df = pd.DataFrame({
            'timestamp': UNIX_Timestamp,
            'Col1': col,
        })
        expected_df.set_index('timestamp', inplace=True) 

        # Validate
        pd.testing.assert_frame_equal(actual_df, expected_df, check_dtype=True)

if __name__ =="__main__":
    unittest.main()