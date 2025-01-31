import unittest
from datetime import datetime
from ibapi.contract import Contract

from midastrader.structs.events import OrderEvent
from midastrader.structs.orders import Action, MarketOrder


class TestOrderEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = 1651500000
        self.action = Action.LONG
        self.trade_id = 2
        self.leg_id = 6
        self.order = MarketOrder(self.action, 10)
        self.contract = Contract()

    # Basic Validation
    def test_basic_validation(self):
        # Test
        event = OrderEvent(
            timestamp=self.timestamp,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
            action=self.action,
            order=self.order,
            contract=self.contract,
        )
        # Validate
        self.assertEqual(event.timestamp, self.timestamp)
        self.assertEqual(event.order, self.order)
        self.assertEqual(event.contract, self.contract)
        self.assertEqual(event.action, self.action)
        self.assertEqual(event.trade_id, self.trade_id)
        self.assertEqual(event.leg_id, self.leg_id)

    # Type Checks
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            OrderEvent(
                timestamp=datetime(2024, 1, 1),  # pyright: ignore
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                action=self.action,
                order=self.order,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'trade_id' must be of type int."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id="1",  # pyright: ignore
                leg_id=self.leg_id,
                action=self.action,
                order=self.order,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'leg_id' must be of type int."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=self.trade_id,
                leg_id="2",  # pyright: ignore
                action=self.action,
                order=self.order,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'action' must be of type Action enum."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                action=123,  # pyright: ignore
                order=self.order,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'contract' must be of type Contract."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                action=self.action,
                order=self.order,
                contract="self.contract",  # pyright: ignore
            )

        with self.assertRaisesRegex(
            TypeError, "'order' must be of type BaseOrder."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                action=self.action,
                order="self.order",  # pyright: ignore
                contract=self.contract,
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'trade_id' must be greater than zero."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=0,
                leg_id=self.leg_id,
                action=self.action,
                order=self.order,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            ValueError, "'leg_id' must be greater than zero."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                trade_id=1,
                leg_id=0,
                action=self.action,
                order=self.order,
                contract=self.contract,
            )


if __name__ == "__main__":
    unittest.main()
