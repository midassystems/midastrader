import unittest
import pandas as pd
from midastrader.utils.unix import (
    unix_to_iso,
    iso_to_unix,
    unix_to_date,
    resample_timestamp,
)
import datetime


class TestUtils(unittest.TestCase):
    def test_iso_to_unix_tz_aware(self):
        iso_timestamp = "2024-02-07T12:00:00+00:00"

        # Test
        unix_timestamp = iso_to_unix(iso_timestamp)

        # Valdiate
        self.assertEqual(unix_timestamp, 1707307200000000000)

    def test_iso_to_unix_naive(self):
        date_str = "2021-11-01T01:01:01Z"

        # Test
        unix_nanos = iso_to_unix(date_str)

        # Validate
        self.assertEqual(1635728461000000000, unix_nanos)

    def test_unix_to_iso_utc(self):
        unix = 1635728461000000000

        # Test
        iso = unix_to_iso(unix)

        # Validate
        self.assertEqual("2021-11-01T01:01:01+00:00", iso)

    def test_unix_to_ios_EST(self):
        unix_timestamp = 1679789200000000000

        # Test
        iso_timestamp = unix_to_iso(unix_timestamp, "US/Eastern")

        # Valdiate
        self.assertEqual(iso_timestamp, "2023-03-25T20:06:40-04:00")

    def test_unix_to_date(self):
        unix = 1635728461000000000

        # Test
        date = unix_to_date(unix)

        # Validate
        self.assertEqual(datetime.date(2021, 11, 1), date)

    def test_resample_daily(self):
        df = pd.DataFrame(
            {
                "timestamp": [
                    1704098576204104704,
                    1704119427481684736,
                    1704159224811226368,
                    1704203604070369024,
                    1704254892183270144,
                    1704312309960591616,
                    1704354268672059648,
                    1704399080573728256,
                    1704450706695355136,
                    1704497748117854720,
                    1704540253016760064,
                    1704573685899493888,
                    1704629115124939264,
                    1704673128279459840,
                ],
                "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5],
            }
        ).set_index("timestamp")

        # Test
        daily_df = resample_timestamp(df)

        # Excpected
        expected_df = pd.DataFrame(
            {
                "timestamp": [
                    1704119427481684736,
                    1704203604070369024,
                    1704312309960591616,
                    1704399080573728256,
                    1704497748117854720,
                    1704573685899493888,
                    1704629115124939264,
                    1704673128279459840,
                ],
                "data": [2, 4, 6, 8, 1, 3, 4, 5],
            }
        ).set_index("timestamp")

        # Validate
        pd.testing.assert_frame_equal(daily_df, expected_df)


if __name__ == "__main__":
    unittest.main()
