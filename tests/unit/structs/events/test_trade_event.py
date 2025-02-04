import unittest

from midastrader.structs.trade import Trade
from midastrader.structs.orders import Action
from midastrader.structs.events import TradeCommissionEvent, TradeEvent
from midastrader.structs.symbol import SecurityType


class TestTradeEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test Data
        self.timetamp = 1651500000
        self.trade_details = Trade(
            timestamp=1651500000,
            trade_id=1,
            signal_id=2,
            instrument=123,
            security_type=SecurityType.STOCK,
            quantity=-10.0,
            avg_price=9.9,
            trade_value=103829083.0,
            trade_cost=9000.99,
            action=Action.LONG.value,
            fees=9.78,
            is_rollover=True,
        )

    # Basic Validation
    def test_valid_construction(self):
        # Test
        event = TradeEvent(
            str(self.trade_details.trade_id),
            self.trade_details,
        )

        # Validation
        self.assertEqual(event.trade_id, str(self.trade_details.trade_id))
        self.assertEqual(event.trade, self.trade_details)

    # Type Check
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'trade_id' must be of type str."
        ):
            TradeEvent(
                1,  # pyright: ignore
                self.trade_details,
            )

        with self.assertRaisesRegex(
            TypeError, "'trade' must be of type Trade instance."
        ):
            TradeEvent(
                "1",
                "testing",  # pyright: ignore
            )


class TestTradeCommissionEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test Data
        self.trade_id = "12345"
        self.commission = 60.0

    # Basic Validation
    def test_valid_construction(self):
        # Test
        event = TradeCommissionEvent(self.trade_id, self.commission)

        # Validation
        self.assertEqual(event.trade_id, self.trade_id)
        self.assertEqual(event.commission, self.commission)

    # Type Check
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'trade_id' must be of type str."
        ):
            TradeCommissionEvent(
                1,  # pyright: ignore
                self.commission,
            )

        with self.assertRaisesRegex(
            TypeError, "'commission' must be of type float."
        ):
            TradeCommissionEvent(
                self.trade_id,
                "testing",  # pyright: ignore
            )


if __name__ == "__main__":
    unittest.main()
