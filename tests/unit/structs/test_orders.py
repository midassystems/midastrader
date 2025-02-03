import unittest
from ibapi.order import Order

from midastrader.structs.orders import (
    Action,
    OrderType,
    MarketOrder,
    LimitOrder,
    StopLoss,
)


class TestAction(unittest.TestCase):
    def setUp(self) -> None:
        self.long = Action.LONG
        self.short = Action.SHORT
        self.sell = Action.SELL
        self.cover = Action.COVER

    # Basic Validation
    def test_long_to_broker_standard(self):
        # Test
        result = self.long.to_broker_standard()

        # Validation
        self.assertEqual("BUY", result)  # LONG should be a 'BUY'

    def test_cover_to_broker_standard(self):
        # Test
        result = self.cover.to_broker_standard()

        # Validation
        self.assertEqual("BUY", result)  # COVER should be a 'BUY'

    def test_sell_to_broker_standard(self):
        # Test
        result = self.sell.to_broker_standard()

        # Validation
        self.assertEqual("SELL", result)  # SELL should be a 'SELL'

    def test_short_to_broker_standard(self):
        # Test
        result = self.short.to_broker_standard()

        # Validation
        self.assertEqual("SELL", result)  # SHORT should be a 'SELL'

    # Type Check
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            Action("INVALID_ACTION")


class TestMarketOrder(unittest.TestCase):
    def setUp(self) -> None:
        # Mock data
        self.instrument_id = 1
        self.signal_id = 1
        self.action = Action.LONG
        self.quantity = 20
        self.order_type = OrderType.MARKET

    # Basic Validation
    def test_valid_construction(self):
        # Test
        order = MarketOrder(
            self.instrument_id,
            self.signal_id,
            self.action,
            self.quantity,
        )

        # Validation
        self.assertEqual(order.action, self.action)
        self.assertEqual(order.quantity, self.quantity)

    def test_ib_order(self):
        # Test
        order = MarketOrder(
            self.instrument_id,
            self.signal_id,
            self.action,
            self.quantity,
        )

        # Validation
        base_order = order.ib_order()
        self.assertEqual(type(base_order), Order)
        self.assertEqual(base_order.action, self.action.to_broker_standard())
        self.assertEqual(base_order.totalQuantity, abs(self.quantity))
        self.assertEqual(base_order.orderType, self.order_type.value)

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG

        # Test
        order = MarketOrder(1, 1, action, quantity)

        # Validation
        base_order = order.ib_order()
        self.assertEqual(base_order.totalQuantity, abs(quantity))
        self.assertEqual(order.quantity, quantity)

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT

        # Test
        order = MarketOrder(1, 1, action, quantity)

        # Validation
        base_order = order.ib_order()
        self.assertEqual(base_order.totalQuantity, abs(quantity))
        self.assertEqual(order.quantity, quantity)

    # Type Check
    def test_type_check(self):
        with self.assertRaisesRegex(
            TypeError, "'action' field must be type Action enum."
        ):
            MarketOrder(
                1,
                1,
                action="self.action,",  # pyright: ignore
                quantity=self.quantity,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' field must be type float or int."
        ):
            MarketOrder(
                1,
                1,
                action=self.action,
                quantity="self.quantity",  # pyright: ignore
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'quantity' field must not be zero."
        ):
            MarketOrder(1, 1, action=self.action, quantity=0.0)


class TestLimitOrder(unittest.TestCase):
    def setUp(self) -> None:
        # Mock data
        self.instrument_id = 2
        self.signal_id = 1
        self.action = Action.LONG
        self.quantity = 20
        self.limit_price = 100.9
        self.order_type = OrderType.LIMIT

    # Basic Validation
    def test_valid_construction(self):
        # Test
        order = LimitOrder(
            self.instrument_id,
            self.signal_id,
            self.action,
            self.quantity,
            self.limit_price,
        )

        # Validation
        self.assertEqual(order.action, self.action)
        self.assertEqual(order.order_type, self.order_type)
        self.assertEqual(order.limit_price, self.limit_price)

    def test_ib_order(self):
        # Test
        order = LimitOrder(
            self.instrument_id,
            self.signal_id,
            self.action,
            self.quantity,
            self.limit_price,
        )

        # Validation
        base_order = order.ib_order()
        self.assertEqual(type(base_order), Order)
        self.assertEqual(base_order.action, self.action.to_broker_standard())
        self.assertEqual(base_order.totalQuantity, abs(self.quantity))
        self.assertEqual(base_order.orderType, self.order_type.value)
        self.assertEqual(base_order.lmtPrice, self.limit_price)

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG

        # Test
        order = LimitOrder(
            self.instrument_id,
            self.signal_id,
            action,
            quantity,
            self.limit_price,
        )
        # Validation
        base_order = order.ib_order()
        self.assertEqual(float(base_order.totalQuantity), float(abs(quantity)))
        self.assertEqual(order.quantity, quantity)

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT

        # Test
        order = LimitOrder(
            self.instrument_id,
            self.signal_id,
            action,
            quantity,
            self.limit_price,
        )

        # Validation
        base_order = order.ib_order()
        self.assertEqual(float(base_order.totalQuantity), float(abs(quantity)))
        self.assertEqual(order.quantity, quantity)

    # Type Check
    def test_type_checks(self):
        with self.assertRaisesRegex(
            TypeError, "'action' field must be type Action enum."
        ):
            LimitOrder(
                1,
                1,
                action="self.action,",  # pyright: ignore
                quantity=self.quantity,
                limit_price=self.limit_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' field must be type float or int."
        ):
            LimitOrder(
                1,
                1,
                action=self.action,
                quantity="self.quantity",  # pyright: ignore
                limit_price=self.limit_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'limit_price' field must be of type float or int."
        ):
            LimitOrder(
                1,
                1,
                action=self.action,
                quantity=self.quantity,
                limit_price="self.limit_price",  # pyright: ignore
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'quantity' field must not be zero."
        ):
            LimitOrder(
                1,
                1,
                action=self.action,
                quantity=0,
                limit_price=self.limit_price,
            )

        with self.assertRaisesRegex(
            ValueError, "'limit_price' field must be greater than zero."
        ):
            LimitOrder(
                1,
                1,
                action=self.action,
                quantity=self.quantity,
                limit_price=0.0,
            )


class TestStopLoss(unittest.TestCase):
    def setUp(self) -> None:
        # Mock data
        self.action = Action.LONG
        self.quantity = 20
        self.aux_price = 100.9
        self.order_type = OrderType.STOPLOSS

    # Basic Validation
    def test_valid_construction(self):
        # Test
        order = StopLoss(
            1,
            1,
            action=self.action,
            quantity=self.quantity,
            aux_price=self.aux_price,
        )
        # Validation
        self.assertEqual(order.action, self.action)
        self.assertEqual(order.quantity, self.quantity)
        self.assertEqual(order.order_type, self.order_type)
        self.assertEqual(order.aux_price, self.aux_price)

    def test_ib_order(self):
        # Test
        order = StopLoss(
            1,
            1,
            action=self.action,
            quantity=self.quantity,
            aux_price=self.aux_price,
        )

        # Validation
        base_order = order.ib_order()
        self.assertEqual(type(base_order), Order)
        self.assertEqual(base_order.action, self.action.to_broker_standard())
        self.assertEqual(base_order.totalQuantity, abs(self.quantity))
        self.assertEqual(base_order.orderType, self.order_type.value)
        self.assertEqual(base_order.auxPrice, self.aux_price)

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG

        # Test
        order = StopLoss(
            1,
            1,
            action=action,
            quantity=quantity,
            aux_price=self.aux_price,
        )
        # Validation
        base_order = order.ib_order()
        self.assertEqual(float(base_order.totalQuantity), float(abs(quantity)))
        self.assertEqual(order.quantity, quantity)

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT

        # Test
        order = StopLoss(
            1,
            1,
            action=action,
            quantity=quantity,
            aux_price=self.aux_price,
        )

        # Validation
        base_order = order.ib_order()
        self.assertEqual(base_order.totalQuantity, abs(quantity))
        self.assertEqual(order.quantity, quantity)

    # Type Check
    def test_type_checks(self):
        with self.assertRaisesRegex(
            TypeError, "'action' field must be type Action enum."
        ):
            StopLoss(
                1,
                1,
                action="self.action,",  # pyright: ignore
                quantity=self.quantity,
                aux_price=self.aux_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' field must be type float or int."
        ):
            StopLoss(
                1,
                1,
                action=self.action,
                quantity="self.quantity",  # pyright: ignore
                aux_price=self.aux_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'aux_price' field must be of type float or int."
        ):
            StopLoss(
                1,
                1,
                action=self.action,
                quantity=self.quantity,
                aux_price="self.aux_price",  # pyright: ignore
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'quantity' field must not be zero."
        ):
            StopLoss(
                1,
                1,
                action=self.action,
                quantity=0,
                aux_price=self.aux_price,
            )

        with self.assertRaisesRegex(
            ValueError, "'aux_price' field must be greater than zero."
        ):
            StopLoss(
                1,
                1,
                action=self.action,
                quantity=self.quantity,
                aux_price=0.0,
            )


if __name__ == "__main__":
    unittest.main()
