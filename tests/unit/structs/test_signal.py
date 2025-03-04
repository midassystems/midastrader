import unittest

from midastrader.structs import OrderType, Action, SignalInstruction


class TestTradeInsructions(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.instrument = 4
        self.order_type = OrderType.MARKET
        self.action = Action.LONG
        self.trade_id = 2
        self.signal_id = 5
        self.weight = 0.483938
        self.quantity = -10.0
        self.limit_price = 100.0
        self.aux_price = 10.0

    # Basic Validation
    def test_construction_market_order(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=self.order_type,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, self.order_type)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.signal_id, self.signal_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)

    def test_construction_limit_order(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.LIMIT,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
            limit_price=self.limit_price,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, OrderType.LIMIT)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.signal_id, self.signal_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)
        self.assertEqual(instructions.limit_price, self.limit_price)

    def test_construction_stop_loss(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.STOPLOSS,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
            aux_price=self.aux_price,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, OrderType.STOPLOSS)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.signal_id, self.signal_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)
        self.assertEqual(instructions.aux_price, self.aux_price)

    def test_market_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.MARKET,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
        )

        # Test
        instructions_dict = instructions.to_dict()

        # Validate
        self.assertEqual(instructions_dict["ticker"], self.instrument)
        self.assertEqual(
            instructions_dict["order_type"], self.order_type.value
        )
        self.assertEqual(instructions_dict["action"], self.action.value)
        self.assertEqual(instructions_dict["signal_id"], self.signal_id)
        self.assertAlmostEqual(instructions_dict["weight"], self.weight, 4)
        self.assertEqual(instructions_dict["quantity"], self.quantity)
        self.assertEqual(instructions_dict["limit_price"], "")
        self.assertEqual(instructions_dict["aux_price"], "")

    def test_limit_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.LIMIT,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
            limit_price=self.limit_price,
        )

        # Test
        instructions_dict = instructions.to_dict()

        # Validate
        self.assertEqual(instructions_dict["ticker"], self.instrument)
        self.assertEqual(
            instructions_dict["order_type"], OrderType.LIMIT.value
        )
        self.assertEqual(instructions_dict["action"], self.action.value)
        self.assertEqual(instructions_dict["signal_id"], self.signal_id)
        self.assertAlmostEqual(instructions_dict["weight"], self.weight, 4)
        self.assertEqual(instructions_dict["quantity"], self.quantity)
        self.assertEqual(instructions_dict["limit_price"], self.limit_price)
        self.assertEqual(instructions_dict["aux_price"], "")

    def test_stop_loss_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.STOPLOSS,
            action=self.action,
            signal_id=self.signal_id,
            weight=self.weight,
            quantity=self.quantity,
            aux_price=self.aux_price,
        )

        # Test
        instructions_dict = instructions.to_dict()

        # Validate
        self.assertEqual(instructions_dict["ticker"], self.instrument)
        self.assertEqual(
            instructions_dict["order_type"], OrderType.STOPLOSS.value
        )
        self.assertEqual(instructions_dict["action"], self.action.value)
        self.assertEqual(instructions_dict["signal_id"], self.signal_id)
        self.assertAlmostEqual(instructions_dict["weight"], self.weight, 4)
        self.assertEqual(instructions_dict["quantity"], self.quantity)
        self.assertEqual(instructions_dict["limit_price"], "")
        self.assertEqual(instructions_dict["aux_price"], self.aux_price)

    # Type Check
    def test_type_checks(self):
        with self.assertRaisesRegex(
            TypeError, "'instrument' field must be of type int."
        ):
            SignalInstruction(
                instrument="1234",  # pyright: ignore
                order_type=self.order_type,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'order_type' must be of type OrderType enum."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type="MKT",  # pyright: ignore
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'action' field must be of type Action enum."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action="LONG",  # pyright: ignore
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'signal_id' field must of type int."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                signal_id="2",  # pyright: ignore
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' field must be of type float."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity="123",  # pyright: ignore
            )

        with self.assertRaisesRegex(
            TypeError,
            "'limit_price' field must be float for OrderType.LIMIT.",
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.LIMIT,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
                limit_price=0,
            )

        with self.assertRaisesRegex(
            TypeError,
            "'aux_price' field must be float for OrderType.STOPLOSS.",
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.STOPLOSS,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
                aux_price=0,
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'signal_id' field must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                signal_id=0,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            ValueError, "'limit_price' field must must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.LIMIT,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
                limit_price=-1.0,
            )

        with self.assertRaisesRegex(
            ValueError, "'aux_price' field must must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.STOPLOSS,
                action=self.action,
                signal_id=self.signal_id,
                weight=self.weight,
                quantity=self.quantity,
                aux_price=-1.0,
            )


if __name__ == "__main__":
    unittest.main()
