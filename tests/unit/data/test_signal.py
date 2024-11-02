import unittest
from midas.orders import OrderType, Action
from midas.signal import SignalInstruction


class TestTradeInsructions(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.instrument = 4
        self.order_type = OrderType.MARKET
        self.action = Action.LONG
        self.trade_id = 2
        self.leg_id = 5
        self.weight = 0.483938
        self.quantity = -10
        self.limit_price = 100
        self.aux_price = 10

    # Basic Validation
    def test_construction_market_order(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=self.order_type,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
            weight=self.weight,
            quantity=self.quantity,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, self.order_type)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.trade_id, self.trade_id)
        self.assertEqual(instructions.leg_id, self.leg_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)

    def test_construction_limit_order(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.LIMIT,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
            weight=self.weight,
            quantity=self.quantity,
            limit_price=self.limit_price,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, OrderType.LIMIT)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.trade_id, self.trade_id)
        self.assertEqual(instructions.leg_id, self.leg_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)
        self.assertEqual(instructions.limit_price, self.limit_price)

    def test_construction_stop_loss(self):
        # Test
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.STOPLOSS,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
            weight=self.weight,
            quantity=self.quantity,
            aux_price=self.aux_price,
        )
        # Validate
        self.assertEqual(instructions.instrument, self.instrument)
        self.assertEqual(instructions.order_type, OrderType.STOPLOSS)
        self.assertEqual(instructions.action, self.action)
        self.assertEqual(instructions.trade_id, self.trade_id)
        self.assertEqual(instructions.leg_id, self.leg_id)
        self.assertEqual(instructions.weight, self.weight)
        self.assertEqual(instructions.quantity, self.quantity)
        self.assertEqual(instructions.aux_price, self.aux_price)

    def test_market_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.MARKET,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
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
        self.assertEqual(instructions_dict["trade_id"], self.trade_id)
        self.assertEqual(instructions_dict["leg_id"], self.leg_id)
        self.assertAlmostEqual(instructions_dict["weight"], self.weight, 4)
        self.assertEqual(instructions_dict["quantity"], self.quantity)
        self.assertEqual(instructions_dict["limit_price"], "")
        self.assertEqual(instructions_dict["aux_price"], "")

    def test_limit_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.LIMIT,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
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
        self.assertEqual(instructions_dict["trade_id"], self.trade_id)
        self.assertEqual(instructions_dict["leg_id"], self.leg_id)
        self.assertAlmostEqual(instructions_dict["weight"], self.weight, 4)
        self.assertEqual(instructions_dict["quantity"], self.quantity)
        self.assertEqual(instructions_dict["limit_price"], self.limit_price)
        self.assertEqual(instructions_dict["aux_price"], "")

    def test_stop_loss_to_dict(self):
        instructions = SignalInstruction(
            instrument=self.instrument,
            order_type=OrderType.STOPLOSS,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
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
        self.assertEqual(instructions_dict["trade_id"], self.trade_id)
        self.assertEqual(instructions_dict["leg_id"], self.leg_id)
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
                instrument="1234",
                order_type=self.order_type,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'order_type' field must be of type OrderType enum."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type="MKT",
                action=self.action,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'action' field must be of type Action enum."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action="LONG",
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'trade_id' field must of type int."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                trade_id="2",
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'leg_id' field must be of type int."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                trade_id=self.trade_id,
                leg_id="2",
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' field must be of type int or float."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=2,
                weight=self.weight,
                quantity="123",
            )

        with self.assertRaisesRegex(
            TypeError,
            "'limit_price' field must be int or float for OrderType.LIMIT.",
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.LIMIT,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError,
            "'aux_price' field must be int or float for OrderType.STOPLOSS.",
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.STOPLOSS,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'trade_id' field must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                trade_id=0,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            ValueError, "'leg_id' field must must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=self.order_type,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=0,
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
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
                limit_price=-1,
            )

        with self.assertRaisesRegex(
            ValueError, "'aux_price' field must must be greater than zero."
        ):
            SignalInstruction(
                instrument=self.instrument,
                order_type=OrderType.STOPLOSS,
                action=self.action,
                trade_id=self.trade_id,
                leg_id=self.leg_id,
                weight=self.weight,
                quantity=self.quantity,
                aux_price=-1,
            )


if __name__ == "__main__":
    unittest.main()
