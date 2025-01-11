import random
import unittest
from datetime import datetime
from ibapi.contract import Contract

from midastrader.structs import Trade, Action
from midastrader.structs.events import ExecutionEvent


class TestExecutionEvent(unittest.TestCase):
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
        self.action = random.choice(
            [Action.LONG, Action.COVER, Action.SELL, Action.SHORT]
        )
        self.contract = Contract()

    # Basic Validation
    def test_valid_construction(self):
        # Test
        exec = ExecutionEvent(
            timestamp=self.timetamp,
            trade_details=self.trade_details,
            action=self.action,
            contract=self.contract,
        )
        # Validation
        self.assertEqual(exec.timestamp, self.timetamp)
        self.assertEqual(exec.action, self.action)
        self.assertEqual(exec.contract, self.contract)
        self.assertEqual(exec.trade_details, self.trade_details)
        self.assertEqual(type(exec.action), Action)
        self.assertEqual(type(exec.contract), Contract)

    # Type Check
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            ExecutionEvent(
                timestamp=datetime(2024, 1, 1),
                trade_details=self.trade_details,
                action=self.action,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'action' must be of type Action enum."
        ):
            ExecutionEvent(
                timestamp=self.timetamp,
                trade_details=self.trade_details,
                action="self.action",
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'trade_details' must be of type Trade instance."
        ):
            ExecutionEvent(
                timestamp=self.timetamp,
                trade_details="self.trade_details,",
                action=self.action,
                contract=self.contract,
            )

        with self.assertRaisesRegex(
            TypeError, "'contract' must be of type Contract instance."
        ):
            ExecutionEvent(
                timestamp=self.timetamp,
                trade_details=self.trade_details,
                action=self.action,
                contract="self.contract",
            )


if __name__ == "__main__":
    unittest.main()
