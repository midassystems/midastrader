import unittest
from datetime import datetime
from midas.engine.events import SignalEvent
from midas.orders import OrderType, Action
from midas.signal import SignalInstruction


class TestSignalEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = 1651500000
        self.trade_capital = 1000090
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=10,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=10,
        )
        self.instructions = [self.trade1, self.trade2]

    # Basic Validation
    def test_construction(self):
        # Test
        signal = SignalEvent(self.timestamp, self.instructions)

        # Validate timestamp
        self.assertEqual(signal.timestamp, self.timestamp)

        # Validate first set of trade instructions
        self.assertEqual(
            signal.instructions[0].instrument, self.trade1.instrument
        )
        self.assertEqual(
            signal.instructions[0].order_type, self.trade1.order_type
        )
        self.assertEqual(signal.instructions[0].action, self.trade1.action)
        self.assertEqual(signal.instructions[0].trade_id, self.trade1.trade_id)
        self.assertEqual(signal.instructions[0].leg_id, self.trade1.leg_id)
        self.assertEqual(signal.instructions[0].weight, self.trade1.weight)

        # Validate second set of trade instructions
        self.assertEqual(
            signal.instructions[1].instrument, self.trade2.instrument
        )
        self.assertEqual(
            signal.instructions[1].order_type, self.trade2.order_type
        )
        self.assertEqual(signal.instructions[1].action, self.trade2.action)
        self.assertEqual(signal.instructions[1].trade_id, self.trade2.trade_id)
        self.assertEqual(signal.instructions[1].leg_id, self.trade2.leg_id)
        self.assertEqual(signal.instructions[1].weight, self.trade2.weight)

    def test_to_dict(self):
        signal = SignalEvent(
            timestamp=self.timestamp,
            instructions=self.instructions,
        )

        # Test
        signal_dict = signal.to_dict()

        # Validation
        self.assertEqual(signal_dict["timestamp"], self.timestamp)
        self.assertEqual(
            len(signal_dict["instructions"]),
            len(self.instructions),
        )  # checkall trade instructions include in serialization

    # Type Check
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' field must be of type int."
        ):
            SignalEvent(
                timestamp=datetime(2024, 1, 1),
                instructions=self.instructions,
            )

        with self.assertRaisesRegex(
            TypeError, "'instructions' field must be of type list."
        ):
            SignalEvent(timestamp=self.timestamp, instructions=self.trade1)

        with self.assertRaisesRegex(
            TypeError,
            "All instructions must be instances of SignalInstruction.",
        ):
            SignalEvent(
                timestamp=self.timestamp, instructions=["sell", "long"]
            )

    # Constraint Check
    def test_value_constraints(self):
        with self.assertRaisesRegex(
            ValueError, "'instructions' list cannot be empty."
        ):
            SignalEvent(timestamp=self.timestamp, instructions=[])


if __name__ == "__main__":
    unittest.main()
