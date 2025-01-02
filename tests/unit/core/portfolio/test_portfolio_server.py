import unittest
import threading
from datetime import time
from ibapi.order import Order
from ibapi.contract import Contract
from time import sleep
from unittest.mock import Mock, MagicMock

from midas.message_bus import MessageBus, EventType
from midas.structs.symbol import SymbolMap
from midas.utils.logger import SystemLogger
from midas.structs.active_orders import ActiveOrder
from midas.structs.account import Account
from midas.structs.positions import EquityPosition
from midas.core.portfolio import PortfolioServer, PortfolioServerManager
from midas.structs.symbol import (
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


class TestPortfolioServerManager(unittest.TestCase):
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
        self.bus = MessageBus()

        # Portfolio server instance
        self.manager = PortfolioServerManager(self.symbols_map, self.bus)
        threading.Thread(target=self.manager.process, daemon=True).start()

        self.server = PortfolioServer.get_instance()

    # Basic Validation
    def test_process_orders(self):
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
        self.bus.publish(EventType.ORDER_UPDATE, active_order)
        sleep(1)

        # Validate
        tickers = self.server.get_active_order_tickers()
        self.assertEqual(tickers, [70])

    def test_process_positions(self):
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
        self.bus.publish(EventType.POSITION_UPDATE, (id, position_data))
        sleep(1)

        # Validate
        positions = self.server.positions
        self.assertEqual(positions, {id: position_data})

    def test_process_account(self):
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
        self.bus.publish(EventType.ACCOUNT_UPDATE, account_data)
        sleep(1)

        # Validate
        account = self.server.account
        self.assertEqual(account, account_data)


if __name__ == "__main__":
    unittest.main()
