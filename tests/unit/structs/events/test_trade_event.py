import unittest

from midas.structs.trade import Trade
from midas.structs.orders import Action
from midas.structs.events import TradeCommissionEvent, TradeEvent


class TestTradeEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test Data
        self.timetamp = 1651500000
        self.trade_details = Trade(
            timestamp=1651500000,
            trade_id=1,
            leg_id=2,
            instrument=123,
            quantity=-10,
            avg_price=9.9,
            trade_value=103829083,
            trade_cost=9000.99,
            action=Action.LONG.value,
            fees=9.78,
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
            TradeEvent(1, self.trade_details)

        with self.assertRaisesRegex(
            TypeError, "'trade' must be of type Trade instance."
        ):
            TradeEvent("1", "testing")


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
            TradeCommissionEvent(1, self.commission)

        with self.assertRaisesRegex(
            TypeError, "'commission' must be of type float."
        ):
            TradeCommissionEvent(self.trade_id, "testing")


if __name__ == "__main__":
    unittest.main()
