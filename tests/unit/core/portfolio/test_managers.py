import unittest
from unittest.mock import Mock

from midas.structs.active_orders import ActiveOrder
from midas.structs.account import Account
from midas.structs.positions import EquityPosition
from midas.core.portfolio.managers import (
    AccountManager,
    PositionManager,
    OrderManager,
)


class TestPositionManager(unittest.TestCase):
    def setUp(self):
        self.manager = PositionManager(Mock())

    def test_update_positions_new_valid(self):
        self.manager.pending_positions_update.add(70)
        self.assertEqual(len(self.manager.pending_positions_update), 1)

        # Position data
        instrument_id = 70
        position = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=100,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )

        # Test
        self.manager.update_positions(70, position)

        # Validate
        self.assertEqual(self.manager.positions[instrument_id], position)
        self.assertEqual(len(self.manager.pending_positions_update), 0)

    def test_update_positions_old_valid(self):
        # Postion data
        instrument_id = 70
        position = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=100,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )

        # Add old position to portfolio server
        self.manager.positions[instrument_id] = position

        # Test
        self.manager.update_positions(instrument_id, position)

        # Validate
        self.assertEqual(self.manager.positions[instrument_id], position)
        self.assertEqual(len(self.manager.positions), 1)

    def test_updated_positions_zero_quantity(self):
        # Old postion
        instrument_id = 70
        position = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=100,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )
        # Add old position to portfolio server
        self.manager.positions[instrument_id] = position

        # Test
        new_position = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=0,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )
        self.manager.update_positions(instrument_id, new_position)

        # Validation
        self.assertEqual(self.manager.positions, {})
        self.assertEqual(len(self.manager.pending_positions_update), 0)

    def test_output_positions(self):
        # Postion data
        instrument_id = 70
        position = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=100,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )

        # Test
        self.manager.update_positions(instrument_id, position)

        # Validation
        self.assertEqual(self.manager.logger.debug.call_count, 1)


class TestOrderManager(unittest.TestCase):
    def setUp(self):
        self.manager = OrderManager(Mock())

    def test_get_active_order_tickers(self):
        self.manager.pending_positions_update.add(1)

        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Add order to portfolio server
        self.manager.active_orders[active_order.permId] = active_order
        active_order.status = "Submitted"

        # Test
        result = self.manager.get_active_order_tickers()

        # Validate
        expected = [1, 70]
        for i in expected:
            self.assertIn(i, result)

    def test_update_orders_new_valid(self):
        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Test
        self.manager.update_orders(active_order)

        # Validation
        self.assertEqual(
            self.manager.active_orders[active_order.permId], active_order
        )

    def test_update_orders_update_valid(self):
        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Add order to portfolio server
        self.manager.active_orders[active_order.permId] = active_order

        # Update order status
        active_order.status = "Submitted"

        # Test
        self.manager.update_orders(active_order)

        # Validation
        self.assertEqual(len(self.manager.active_orders), 1)
        self.assertEqual(
            self.manager.active_orders[active_order.permId], active_order
        )
        self.assertEqual(
            self.manager.active_orders[active_order.permId].status,
            "Submitted",
        )

    def test_update_orders_filled_valid(self):
        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Add order to porfolio server
        self.manager.active_orders[active_order.permId] = active_order
        self.assertEqual(len(self.manager.active_orders), 1)

        # Update order status to filled
        active_order.status = "Filled"

        # Test
        self.manager.update_orders(active_order)

        # Validation
        self.assertEqual(self.manager.active_orders, {})
        self.assertEqual(len(self.manager.active_orders), 0)
        self.assertIn(70, self.manager.pending_positions_update)

    def test_update_orders_cancelled_valid(self):
        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Add order to portfolio server
        self.manager.active_orders[active_order.permId] = active_order
        self.assertEqual(len(self.manager.active_orders), 1)

        # Updated order status
        active_order.status = "Cancelled"

        # Test
        self.manager.update_orders(active_order)

        # Validation
        self.assertEqual(self.manager.active_orders, {})
        self.assertEqual(len(self.manager.active_orders), 0)

    def test_output_orders(self):
        # Order data
        instrument_id = 70
        active_order = ActiveOrder(
            permId=10,
            clientId=1,
            parentId=10,
            orderId=10,
            account="account_name",
            instrument=instrument_id,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=100,
            cashQty=100909,
            lmtPrice=0,
            auxPrice=0,
            status="PreSubmitted",
        )

        # Tests
        self.manager.update_orders(active_order)

        # Validation
        self.assertEqual(self.manager.logger.debug.call_count, 1)


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        # Account data
        self.account_info = Account(
            timestamp=16777700000000,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )
        self.account_manager = AccountManager(Mock())

    def test_update_account_details(self):
        # Test
        self.account_manager.update_account_details(self.account_info)

        # Validation
        self.assertEqual(
            self.account_manager.get_capital, self.account_info.capital
        )


if __name__ == "__main__":
    unittest.main()
