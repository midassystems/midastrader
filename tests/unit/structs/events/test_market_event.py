import unittest
from datetime import datetime
from mbinary import OhlcvMsg, BboMsg, BidAskPair, Side

from midastrader.structs.events import MarketEvent


class TestMarketEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = 1707221160000000000
        self.bar = OhlcvMsg(
            instrument_id=1,
            ts_event=self.timestamp,
            rollover_flag=0,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )
        self.tick = BboMsg(
            instrument_id=1,
            ts_event=self.timestamp,
            rollover_flag=0,
            price=int(12 * 1e9),
            size=12345,
            side=Side.NONE,
            flags=0,
            ts_recv=123456776543,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=11,
                    ask_px=23,
                    bid_sz=123,
                    ask_sz=234,
                    bid_ct=3,
                    ask_ct=4,
                )
            ],
        )

    # Basic Validation
    def test_valid_construction(self):
        # Test
        event = MarketEvent(timestamp=self.timestamp, data=self.bar)
        event2 = MarketEvent(timestamp=self.timestamp, data=self.tick)

        # Validate
        self.assertEqual(event.data, self.bar)
        self.assertEqual(event2.data, self.tick)

    # Type Validation
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            MarketEvent(
                data=self.bar,
                timestamp=datetime(2024, 1, 1),  # pyright: ignore
            )
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            MarketEvent(
                data=self.bar,
                timestamp=None,  # pyright: ignore
            )
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            MarketEvent(
                data=self.bar,
                timestamp="14-10-2020",  # pyright: ignore
            )
        with self.assertRaisesRegex(
            TypeError, "'data' must be of type RecordMsg."
        ):
            MarketEvent(
                data=[1, 2, 3],  # pyright: ignore
                timestamp=self.timestamp,
            )
        with self.assertRaisesRegex(
            TypeError, "'data' must be of type RecordMsg."
        ):
            MarketEvent(
                data={1: 1, 2: 1, 3: 1},  # pyright: ignore
                timestamp=self.timestamp,
            )


if __name__ == "__main__":
    unittest.main()
