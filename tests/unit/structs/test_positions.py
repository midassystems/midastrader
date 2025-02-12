import unittest
from datetime import time

from midastrader.structs import (
    SecurityType,
    Venue,
    Currency,
    Industry,
    Equity,
    Future,
    Option,
    Right,
    ContractUnits,
    TradingSession,
    FuturesMonth,
    FuturePosition,
    EquityPosition,
    OptionPosition,
    Impact,
)
from midastrader.structs.positions import position_factory


class TestFuturePosition(unittest.TestCase):
    def setUp(self) -> None:
        # Postion data
        self.action = "BUY"
        self.avg_price = 80.0
        self.quantity = 5.0
        self.quantity_multiplier = 40000
        self.price_multiplier = 0.01
        self.initial_margin = 5000.0
        self.maintenance_margin = 4000.0
        self.market_price = 90.0

        # Position object
        self.position = FuturePosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
            initial_margin=self.initial_margin,
            maintenance_margin=self.maintenance_margin,
        )

    # Basic Validation
    def test_construction(self):
        # Test
        position = FuturePosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
            initial_margin=self.initial_margin,
            maintenance_margin=self.maintenance_margin,
        )

        # Expected
        initial_value = (self.avg_price * self.price_multiplier) * (
            self.quantity_multiplier * self.quantity
        )
        initial_cost = self.initial_margin * abs(self.quantity)
        market_value = (
            self.quantity
            * self.quantity_multiplier
            * self.market_price
            * self.price_multiplier
        )
        init_margin_required = self.initial_margin * self.quantity
        maint_margin_required = self.maintenance_margin * self.quantity

        unrealized_pnl = (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )
        liquidation_value = (self.initial_margin * abs(self.quantity)) + (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

        # Validate
        self.assertEqual(type(position), FuturePosition)
        self.assertEqual(initial_value, position.initial_value)
        self.assertEqual(initial_cost, position.initial_cost)
        self.assertEqual(market_value, position.market_value)
        self.assertEqual(unrealized_pnl, position.unrealized_pnl)
        self.assertEqual(init_margin_required, position.init_margin_required)
        self.assertEqual(
            maint_margin_required, position.maintenance_margin_required
        )
        self.assertEqual(liquidation_value, position.liquidation_value)

    def test_position_impact(self):
        current_price = 25
        self.position.market_price = current_price

        # Test
        impact = self.position.position_impact()

        # Expected
        expected_impact = Impact(
            init_margin_required=abs(self.quantity) * self.initial_margin,
            maintenance_margin_required=abs(self.quantity)
            * self.maintenance_margin,
            unrealized_pnl=(
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),
            liquidation_value=abs(self.quantity) * self.initial_margin
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),
            cash=self.quantity * self.initial_margin * -1,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_full_exit(self):
        current_price = 25
        market_price = 25
        quantity = -self.quantity
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=0,
            liquidation_value=0,
            cash=(abs(quantity) * self.initial_margin)
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * abs(quantity)
                * self.quantity_multiplier
            ),
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_add(self):
        current_price = 25
        market_price = 25
        quantity = 5
        action = "BUY"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=(self.quantity + quantity)
            * self.initial_margin,
            maintenance_margin_required=(self.quantity + quantity)
            * self.maintenance_margin,
            unrealized_pnl=(
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),
            liquidation_value=(
                abs(quantity + self.quantity) * self.initial_margin
            )
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),
            cash=-quantity * self.initial_margin,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_partial_exit(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity - 2)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=(self.quantity + quantity)
            * self.initial_margin,
            maintenance_margin_required=(self.quantity + quantity)
            * self.maintenance_margin,
            unrealized_pnl=(
                (current_price - self.avg_price)
                * self.price_multiplier
                * (self.quantity - abs(quantity))
                * self.quantity_multiplier
            ),  # pnl on the quantity not sold
            liquidation_value=(
                abs(self.quantity + quantity) * self.initial_margin
            )
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * (self.quantity - abs(quantity))
                * self.quantity_multiplier
            ),  # margin and unrealized pnl for quantity still held
            cash=(abs(quantity) * self.initial_margin)
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * abs(quantity)
                * self.quantity_multiplier
            ),  # release of margin for quantity sold adjust for pnl on quantity sold
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_flip_position(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity + 10)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity,
            current_price,
            market_price,
            action,
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=abs(self.quantity + quantity)
            * self.initial_margin,  # remaining quantity * margin per contract
            maintenance_margin_required=abs(self.quantity + quantity)
            * self.maintenance_margin,  # remaining quantity * margin per contract
            unrealized_pnl=0,  # no unrealized pnl as all units remaining  are new
            liquidation_value=(
                abs(self.quantity + quantity) * self.initial_margin
            ),  # margin posted for new quantity, no unrealized pnl as just entered
            cash=(abs(self.quantity) * self.initial_margin)
            - (abs(self.quantity + quantity) * self.initial_margin)
            + (
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),  # release of margin for quantity adjust for new margin posted and pnl on quantity sold
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    # Type/Constraint Validation
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'action' must be of type str."
        ):
            FuturePosition(
                action=1234,  # pyright: ignore
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
                initial_margin=self.initial_margin,
            )

        with self.assertRaisesRegex(
            TypeError, "'avg_price' must be of type int or float."
        ):
            FuturePosition(
                action="BUY",
                avg_price="1234",  # pyright: ignore
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' must be of type int or float."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity="1234",  # pyright: ignore
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'price_multiplier' must be of type int or float."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier="1234",  # pyright: ignore
                quantity=self.quantity,
                quantity_multiplier=1234,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity_multiplier' must be of type int."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier="1234",  # pyright: ignore
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'initial_margin' must be of type int or float."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin="1234",  # pyright: ignore
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'market_price' must be of type int or float."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=self.initial_margin,
                market_price="1234",  # pyright: ignore
            )

        # with self.assertRaisesRegex(TypeError, "'unrealized_pnl' must be of type int or float."):
        #     FuturePosition(
        #                 action="BUY",
        #                 avg_price=self.avg_price,
        #                 price_multiplier=self.price_multiplier,
        #                 quantity=self.quantity,
        #                 quantity_multiplier=self.quantity_multiplier,
        #                 initial_margin=self.initial_margin,
        #                 unrealized_pnl="1234",
        #                 market_v=1234
        #             )

    def test_value_constraints(self):
        with self.assertRaises(ValueError):
            FuturePosition(
                action="BUY1",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'price_multiplier' and 'quantity_multiplier' must be greater than zero.",
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=0,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'price_multiplier' and 'quantity_multiplier' must be greater than zero.",
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=0,
                initial_margin=self.initial_margin,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            ValueError, "'initial_margin' must be non-negative."
        ):
            FuturePosition(
                action="BUY",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                initial_margin=-1,
                market_price=self.market_price,
            )


class TestEquityPosition(unittest.TestCase):
    def setUp(self) -> None:
        # Position data
        self.action = "BUY"
        self.avg_price = 10.0
        self.quantity = 100.0
        self.quantity_multiplier = 1
        self.price_multiplier = 1.00
        self.initial_margin = 0.0
        self.maintenance_margin = 0.0
        self.market_price = 20.0

        # Position object
        self.position = EquityPosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
        )

    # Basic Validation
    def test_construction(self):
        # Test
        position = EquityPosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
        )

        # Expected
        initial_value = self.avg_price * self.quantity
        initial_cost = self.avg_price * self.quantity
        market_value = self.market_price * self.quantity
        unrealized_pnl = market_value - initial_value
        init_margin_required = 0
        maint_margin_required = 0
        liquidation_value = self.market_price * self.quantity

        # Validate
        self.assertEqual(type(position), EquityPosition)
        self.assertEqual(initial_value, position.initial_value)
        self.assertEqual(initial_cost, position.initial_cost)
        self.assertEqual(market_value, position.market_value)
        self.assertEqual(unrealized_pnl, position.unrealized_pnl)
        self.assertEqual(liquidation_value, position.liquidation_value)
        self.assertEqual(init_margin_required, position.init_margin_required)
        self.assertEqual(
            maint_margin_required, position.maintenance_margin_required
        )

    def test_position_impact(self):
        current_price = 25
        self.position.market_price = current_price

        # Test
        impact = self.position.position_impact()

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=((current_price - self.avg_price) * self.quantity),
            liquidation_value=(current_price * self.quantity),
            cash=self.quantity * self.avg_price * -1,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_full_exit(self):
        current_price = 25
        market_price = 25
        quantity = -self.quantity
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=0,
            liquidation_value=0,
            cash=(current_price * abs(quantity)),
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_add(self):
        current_price = 25
        market_price = 25
        quantity = self.quantity
        action = "BUY"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=(current_price - self.avg_price) * self.quantity,
            liquidation_value=current_price * (self.quantity + quantity),
            cash=current_price * quantity * -1,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_partial_exit(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity - 2)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=(current_price - self.avg_price)
            * (abs(self.quantity + quantity)),
            liquidation_value=abs(self.quantity + quantity) * current_price,
            cash=(current_price * abs(quantity)),
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_flip_position(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity + 10)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity, current_price, market_price, action
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=0,
            liquidation_value=(self.quantity + quantity) * current_price,
            cash=(current_price * abs(quantity)),
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    # Type/Constraint Validation
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'action' must be of type str."
        ):
            EquityPosition(
                action=1234,  # pyright: ignore
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'avg_price' must be of type int or float."
        ):
            EquityPosition(
                action="BUY",
                avg_price="1234",  # pyright: ignore
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity' must be of type int or float."
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity="1234",  # pyright: ignore
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'price_multiplier' must be of type int or float."
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier="1234",  # pyright: ignore
                quantity=self.quantity,
                quantity_multiplier=1234,
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'quantity_multiplier' must be of type int."
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier="1234",  # pyright: ignore
                market_price=self.market_price,
            )

        with self.assertRaisesRegex(
            TypeError, "'market_price' must be of type int or float."
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price="1234",  # pyright: ignore
            )

    def test_value_constraints(self):
        with self.assertRaises(ValueError):
            EquityPosition(
                action="long",
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=1234,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'price_multiplier' and 'quantity_multiplier' must be greater than zero.",
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=0,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=1234,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'price_multiplier' and 'quantity_multiplier' must be greater than zero.",
        ):
            EquityPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=0,
                market_price=1234,
            )


class TestOptionPosition(unittest.TestCase):
    def setUp(self) -> None:
        # Position data
        self.action = "BUY"
        self.avg_price = 10
        self.quantity = 100
        self.quantity_multiplier = 100
        self.price_multiplier = 1
        self.market_price = 11
        self.strike_price = 100
        self.expiration_date = "20240808"
        self.type = Right.CALL

        # Position object
        self.position = OptionPosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
            strike_price=self.strike_price,
            expiration_date=self.expiration_date,
            type=self.type,
        )

    # Basic Validation
    def test_construction(self):
        # Test
        position = OptionPosition(
            action=self.action,
            avg_price=self.avg_price,
            price_multiplier=self.price_multiplier,
            quantity=self.quantity,
            quantity_multiplier=self.quantity_multiplier,
            market_price=self.market_price,
            strike_price=self.strike_price,
            expiration_date=self.expiration_date,
            type=self.type,
        )

        # Expected
        initial_value = (
            self.avg_price * self.quantity * self.quantity_multiplier
        )
        initial_cost = (
            -initial_value if self.action == "BUY" else initial_value
        )
        market_value = (
            self.quantity
            * self.quantity_multiplier
            * self.market_price
            * self.price_multiplier
        )
        init_margin_required = 0
        maintenance_margin_required = 0
        unrealized_pnl = (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )
        liquidation_value = (
            self.quantity
            * self.quantity_multiplier
            * self.market_price
            * self.price_multiplier
        )

        # Validate
        self.assertEqual(type(position), OptionPosition)
        self.assertEqual(initial_value, position.initial_value)
        self.assertEqual(initial_cost, position.initial_cost)
        self.assertEqual(market_value, position.market_value)
        self.assertEqual(init_margin_required, position.init_margin_required)
        self.assertEqual(
            maintenance_margin_required, position.maintenance_margin_required
        )
        self.assertEqual(unrealized_pnl, position.unrealized_pnl)
        self.assertEqual(liquidation_value, position.liquidation_value)

    def test_position_impact(self):
        current_price = 25
        self.position.market_price = current_price

        # Test
        impact = self.position.position_impact()

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=(
                (current_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            ),
            liquidation_value=current_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier,
            cash=self.quantity * self.avg_price * self.quantity_multiplier,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    def test_update_add(self):
        current_price = 25
        market_price = 25
        quantity = self.quantity
        action = "BUY"

        # Test
        impact = self.position.update(
            quantity,
            current_price,
            market_price,
            action,
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=(current_price - self.avg_price)
            * self.quantity
            * self.quantity_multiplier,
            liquidation_value=abs(self.quantity + quantity)
            * current_price
            * self.quantity_multiplier,
            cash=(current_price * abs(quantity)) * self.quantity_multiplier,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    # TODO: Not PASSING
    def test_update_partial_exit(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity - 2)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity,
            current_price,
            market_price,
            action,
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=(current_price - self.avg_price)
            * abs(self.quantity + quantity)
            * self.quantity_multiplier,
            liquidation_value=abs(self.quantity + quantity)
            * current_price
            * self.quantity_multiplier,
            cash=(current_price * abs(quantity)) * self.quantity_multiplier,
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    # TODO: Not PASSING
    def test_update_flip_position(self):
        current_price = 25
        market_price = 25
        quantity = -(self.quantity + 10)
        action = "SELL"

        # Test
        impact = self.position.update(
            quantity,
            current_price,
            market_price,
            action,
        )

        # Expected
        expected_impact = Impact(
            init_margin_required=0,
            maintenance_margin_required=0,
            unrealized_pnl=0,
            liquidation_value=(quantity + self.quantity)
            * current_price
            * self.quantity_multiplier,
            cash=(current_price * (self.quantity) * self.quantity_multiplier)
            + (10 * current_price * self.quantity_multiplier),
        )

        # Validate
        self.assertAlmostEqual(
            expected_impact.init_margin_required, impact.init_margin_required
        )
        self.assertAlmostEqual(
            expected_impact.maintenance_margin_required,
            impact.maintenance_margin_required,
        )
        self.assertAlmostEqual(
            expected_impact.unrealized_pnl, impact.unrealized_pnl
        )
        self.assertAlmostEqual(
            expected_impact.liquidation_value, impact.liquidation_value
        )
        self.assertAlmostEqual(expected_impact.cash, impact.cash)

    # Type/Value Constraints
    def test_type_check(self):
        with self.assertRaisesRegex(
            TypeError, "'type' must be of type Right enum."
        ):
            OptionPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                type="CALL",  # pyright: ignore
            )

        with self.assertRaisesRegex(
            TypeError, "'expiration_date' must be of type str."
        ):
            OptionPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
                strike_price=self.strike_price,
                expiration_date=1234,  # pyright: ignore
                type=self.type,
            )

        with self.assertRaisesRegex(
            TypeError, "'strike_price' must be of type int or float."
        ):
            OptionPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
                strike_price="186",  # pyright: ignore
                expiration_date="202408",
                type=self.type,
            )

    def test_value_check(self):
        with self.assertRaisesRegex(
            ValueError, "'strike_price' must be greater than zero."
        ):
            OptionPosition(
                action=self.action,
                avg_price=self.avg_price,
                price_multiplier=self.price_multiplier,
                quantity=self.quantity,
                quantity_multiplier=self.quantity_multiplier,
                market_price=self.market_price,
                strike_price=0,
                expiration_date="202408",
                type=self.type,
            )


class TestPositionfactory(unittest.TestCase):
    def test_create_equity(self):
        asset_type = SecurityType.STOCK

        # Symbol object
        symbol = Equity(
            instrument_id=1,
            broker_ticker="AAPL",
            data_ticker="AAPL2",
            midas_ticker="AAPL",
            security_type=SecurityType.STOCK,
            currency=Currency.USD,
            exchange=Venue.NASDAQ,
            fees=0.1,
            initial_margin=0,
            maintenance_margin=0,
            quantity_multiplier=1,
            price_multiplier=1,
            company_name="Apple Inc.",
            industry=Industry.TECHNOLOGY,
            market_cap=10000000000.99,
            shares_outstanding=1937476363,
            slippage_factor=1,
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
        )

        # Raw position data
        data = {
            "action": "BUY",
            "avg_price": 10.90,
            "quantity": 100,
            "market_price": 1000.90,
        }

        # Test
        result = position_factory(asset_type, symbol, **data)

        # Validate
        self.assertIsInstance(result, EquityPosition)

    def test_create_future(self):
        asset_type = SecurityType.FUTURE

        # Symbol object
        symbol = Future(
            instrument_id=1,
            broker_ticker="HEJ4",
            data_ticker="HE",
            midas_ticker="HE.n.0",
            security_type=SecurityType.FUTURE,
            currency=Currency.USD,
            exchange=Venue.CME,
            fees=0.1,
            initial_margin=4000.598,
            maintenance_margin=4000.0,
            quantity_multiplier=40000,
            price_multiplier=0.01,
            product_code="HE",
            product_name="Lean Hogs",
            industry=Industry.AGRICULTURE,
            contract_size=40000,
            contract_units=ContractUnits.POUNDS,
            tick_size=0.00025,
            min_price_fluctuation=10,
            continuous=False,
            lastTradeDateOrContractMonth="202406",
            slippage_factor=1,
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
            expr_months=[FuturesMonth.G, FuturesMonth.J],
            term_day_rule="nth_business_day_10",
            market_calendar="CMEGlobex_Lean_Hog",
        )

        # Raw position data
        data = {
            "action": "BUY",
            "avg_price": 10.90,
            "quantity": 100,
            "market_price": 123,
        }

        # Test
        result = position_factory(asset_type, symbol, **data)

        # Validate
        self.assertIsInstance(result, FuturePosition)

    def test_create_option(self):
        asset_type = SecurityType.OPTION

        # Symbol object
        symbol = Option(
            instrument_id=1,
            broker_ticker="AAPLP",
            data_ticker="AAPLP",
            midas_ticker="AAPLP",
            security_type=SecurityType.OPTION,
            currency=Currency.USD,
            exchange=Venue.NASDAQ,
            fees=0.1,
            initial_margin=0,
            maintenance_margin=0,
            quantity_multiplier=100,
            price_multiplier=1,
            strike_price=109.99,
            expiration_date="2024-01-01",
            option_type=Right.CALL,
            contract_size=100,
            underlying_name="AAPL",
            lastTradeDateOrContractMonth="20240201",
            slippage_factor=1,
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
        )

        # RAw position data
        data = {
            "action": "BUY",
            "avg_price": 10.90,
            "quantity": 100,
            "market_price": 12,
            "strike_price": 10,
            "expiration_date": "202405",
            "type": Right.CALL,
        }

        # Test
        result = position_factory(asset_type, symbol, **data)

        # Validate
        self.assertIsInstance(result, OptionPosition)


if __name__ == "__main__":
    unittest.main()
