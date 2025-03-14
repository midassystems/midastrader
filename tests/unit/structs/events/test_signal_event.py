import unittest
from datetime import datetime

from midastrader.structs.events import SignalEvent
from midastrader.structs.orders import OrderType, Action
from midastrader.structs.signal import SignalInstruction


class TestSignalEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = 1651500000
        self.trade_capital = 1000090
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            signal_id=2,
            weight=0.5,
            quantity=10.0,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            signal_id=2,
            weight=0.5,
            quantity=10.0,
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
        self.assertEqual(
            signal.instructions[0].signal_id, self.trade1.signal_id
        )
        self.assertEqual(signal.instructions[0].weight, self.trade1.weight)

        # Validate second set of trade instructions
        self.assertEqual(
            signal.instructions[1].instrument, self.trade2.instrument
        )
        self.assertEqual(
            signal.instructions[1].order_type, self.trade2.order_type
        )
        self.assertEqual(signal.instructions[1].action, self.trade2.action)
        self.assertEqual(
            signal.instructions[1].signal_id, self.trade2.signal_id
        )
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
            TypeError, "'timestamp' must be of type int."
        ):
            SignalEvent(
                timestamp=datetime(2024, 1, 1),  # pyright: ignore
                instructions=self.instructions,
            )

        with self.assertRaisesRegex(
            TypeError, "'instructions' must be of type list."
        ):
            SignalEvent(
                timestamp=self.timestamp,
                instructions=self.trade1,  # pyright: ignore
            )

        with self.assertRaisesRegex(
            TypeError,
            "All instructions must be SignalInstruction.",
        ):
            SignalEvent(
                timestamp=self.timestamp,
                instructions=["sell", "long"],  # pyright: ignore
            )

    # Constraint Check
    def test_value_constraints(self):
        with self.assertRaisesRegex(
            ValueError, "'instructions' list cannot be empty."
        ):
            SignalEvent(
                timestamp=self.timestamp,
                instructions=[],
            )


if __name__ == "__main__":
    unittest.main()
