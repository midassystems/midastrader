import unittest
from datetime import time
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import Mock, MagicMock
from midas.symbol import SymbolMap
from midas.utils.logger import SystemLogger
from midas.active_orders import ActiveOrder
from midas.account import Account
from midas.engine.components.observer import EventType
from midas.positions import EquityPosition
from midas.engine.components.portfolio_server import (
    PortfolioServer,
    AccountManager,
    PositionManager,
    OrderManager,
)
from midas.symbol import (
    Equity,
    Currency,
    Venue,
    Future,
    Industry,
    ContractUnits,
    SecurityType,
    FuturesMonth,
    TradingSession,
)


class TestPortfolioServer(unittest.TestCase):
    def setUp(self) -> None:
        # Test symbols
        hogs = Future(
            instrument_id=1,
            broker_ticker="HEJ4",
            data_ticker="HE",
            midas_ticker="HE.n.0",
            security_type=SecurityType.FUTURE,
            fees=0.85,
            currency=Currency.USD,
            exchange=Venue.CME,
            initial_margin=4564.17,
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
            slippage_factor=10,
            lastTradeDateOrContractMonth="202404",
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
            expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
            term_day_rule="nth_business_day_10",
            market_calendar="CMEGlobex_Lean_Hog",
        )
        aapl = Equity(
            instrument_id=2,
            broker_ticker="AAPL",
            data_ticker="AAPL2",
            midas_ticker="AAPL",
            security_type=SecurityType.STOCK,
            currency=Currency.USD,
            exchange=Venue.NASDAQ,
            fees=0.1,
            initial_margin=0,
            quantity_multiplier=1,
            price_multiplier=1,
            company_name="Apple Inc.",
            industry=Industry.TECHNOLOGY,
            market_cap=10000000000.99,
            shares_outstanding=1937476363,
            slippage_factor=10,
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
        )

        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(hogs)
        self.symbols_map.add_symbol(aapl)

        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # Portfolio server instance
        self.portfolio_server = PortfolioServer(symbols_map=self.symbols_map)

    # Basic Validation
    def test_handle_event_order(self):
        # Order data
        instrument_id = 70
        order_id = 10
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "NASDAQ"
        order = Order()
        order.permId = 10
        order.clientId = 1
        order.account = "account_name"
        order.action = "BUY"
        order.orderType = "MKT"
        order.totalQuantity = 100
        order.cashQty = 100909
        order.lmtPrice = 0
        order.auxPrice = 0
        order_state = Mock()
        order_state.status = "PreSubmitted"

        # Create order
        active_order = ActiveOrder(
            permId=order.permId,
            clientId=order.clientId,
            parentId=order.parentId,
            orderId=order_id,
            account=order.account,
            instrument=instrument_id,
            secType=contract.secType,
            exchange=contract.exchange,
            action=order.action,
            orderType=order.orderType,
            totalQty=order.totalQuantity,
            cashQty=order.cashQty,
            lmtPrice=order.lmtPrice,
            auxPrice=order.auxPrice,
            status=order_state.status,
        )

        # Test
        self.portfolio_server.handle_event(
            Mock(),
            EventType.ORDER_UPDATE,
            active_order,
        )

        # Validate
        tickers = self.portfolio_server.get_active_order_tickers()
        self.assertEqual(tickers, [70])

    def test_handle_event_position(self):
        # Position data
        contract = Contract()
        contract.symbol = "AAPL"
        position_data = EquityPosition(
            action="BUY",
            avg_price=10.90,
            quantity=100,
            quantity_multiplier=10,
            price_multiplier=0.01,
            market_price=12,
        )
        id = 1

        # Test
        self.portfolio_server.handle_event(
            Mock(),
            EventType.POSITION_UPDATE,
            id,
            position_data,
        )

        # Validate
        positions = self.portfolio_server.get_positions
        self.assertEqual(positions, {id: position_data})

    def test_handle_event_account(self):
        # Account data
        account_data = Account(
            timestamp=16777700000000,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )

        # Test
        self.portfolio_server.handle_event(
            Mock(),
            EventType.ACCOUNT_UPDATE,
            account_data,
        )

        # Validate
        account = self.portfolio_server.get_account
        self.assertEqual(account, account_data)


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
