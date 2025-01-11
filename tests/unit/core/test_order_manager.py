import unittest
import threading
from time import sleep
from datetime import time
from unittest.mock import Mock, MagicMock
from ibapi.contract import Contract

from midastrader.structs.account import Account
from midastrader.structs.signal import SignalInstruction
from midastrader.core.adapters.order_manager import OrderExecutionManager
from midastrader.utils.logger import SystemLogger
from midastrader.core.adapters.portfolio import PortfolioServer
from midastrader.core.adapters.order_book import OrderBook
from midastrader.structs.events import SignalEvent, OrderEvent
from midastrader.structs.symbol import (
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
from midastrader.structs.orders import (
    MarketOrder,
    LimitOrder,
    StopLoss,
    OrderType,
    Action,
)
from midastrader.structs.symbol import SymbolMap
from midastrader.message_bus import MessageBus, EventType


class TestOrderManager(unittest.TestCase):
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

        self.order_book = OrderBook.get_instance()
        self.order_book._book = {}
        self.portfolio_server = PortfolioServer.get_instance()
        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(hogs)
        self.symbols_map.add_symbol(aapl)

        # Test account
        self.portfolio_server.account_manager.account = Account(
            timestamp=1704214800000000000,
            full_available_funds=502398.7799999999,
            full_init_margin_req=497474.57,
            net_liquidation=999873.3499999999,
            unrealized_pnl=1234,
            full_maint_margin_req=12345,
            excess_liquidity=9876543,
            currency="USD",
            buying_power=765432,
            futures_pnl=76543,
            total_cash_balance=4321,
        )
        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # OrderManager instance
        self.bus = MessageBus()
        self.manager = OrderExecutionManager(
            self.symbols_map,
            self.bus,
        )
        threading.Thread(target=self.manager.process, daemon=True).start()

        # Test Data
        self.timestamp = 1651500000
        self.trade_capital = 10000
        self.trade_equity = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=2,
        )
        self.trade_fut = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.SHORT,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=-2,
        )
        self.trade_instructions = [self.trade_equity, self.trade_fut]
        self.signal_event = SignalEvent(
            self.timestamp, self.trade_instructions
        )

    # Basic Validation
    def test_process(self):
        self.portfolio_server.get_active_order_tickers = Mock(
            return_value=[1, 2]
        )
        self.manager.handle_event = MagicMock()

        # Test
        self.bus.publish(EventType.SIGNAL, self.signal_event)
        sleep(1)

        # Validate
        args = self.manager.handle_event.call_args[0]
        self.assertEqual(args[0], self.signal_event)

    def test_create_marketorder_valid(self):
        self.manager._set_order = Mock()
        self.order_book.retrieve = Mock(return_value=150)

        # Test
        self.manager._handle_signal(self.timestamp, [self.trade_equity])

        # Validation
        args = self.manager._set_order.call_args[0]
        self.assertEqual(type(args[5]), MarketOrder)
        self.assertEqual(args[3], self.trade_equity.action)
        self.assertEqual(
            args[5].order.totalQuantity, abs(self.trade_equity.quantity)
        )

    def test_create_limitorder_valid(self):
        trade_instructions = SignalInstruction(
            instrument=1,
            order_type=OrderType.LIMIT,
            action=Action.SHORT,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=-2,
            limit_price=90,
        )
        self.manager._set_order = Mock()
        self.order_book.retrieve = Mock(return_value=150)

        # Test
        self.manager._handle_signal(self.timestamp, [trade_instructions])

        # Validation
        args = self.manager._set_order.call_args[0]
        self.assertEqual(type(args[5]), LimitOrder)
        self.assertEqual(args[3], trade_instructions.action)
        self.assertEqual(
            args[5].order.totalQuantity, abs(trade_instructions.quantity)
        )
        self.assertEqual(
            args[5].order.lmtPrice, trade_instructions.limit_price
        )

    def test_create_stoplossorder_valid(self):
        trade_instructions = SignalInstruction(
            instrument=1,
            order_type=OrderType.STOPLOSS,
            action=Action.SHORT,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=-2,
            aux_price=90,
        )
        self.manager._set_order = Mock()
        self.order_book.retrieve = Mock(return_value=150)

        # Test
        self.manager._handle_signal(self.timestamp, [trade_instructions])

        # Validation
        args = self.manager._set_order.call_args[0]
        self.assertEqual(type(args[5]), StopLoss)
        self.assertEqual(args[3], trade_instructions.action)
        self.assertEqual(
            args[5].order.totalQuantity, abs(trade_instructions.quantity)
        )
        self.assertEqual(args[5].order.auxPrice, trade_instructions.aux_price)

    def test_handle_signal_sufficient_captial(self):
        self.portfolio_server.account_manager.capital = 10000
        self.order_book.current_price = Mock(return_value=150)
        self.portfolio_server.account.full_init_margin_req = 1000
        self.portfolio_server.account.full_available_funds = 50000
        self.manager._set_order = MagicMock()
        self.order_book.retrieve = Mock(return_value=10)  # current price

        # Test Order Set b/c funds available
        self.manager._handle_signal(self.timestamp, self.trade_instructions)

        # Validate
        self.assertTrue(self.manager._set_order.call_count > 0)

    def test_handle_signal_insufficient_capital(self):
        self.portfolio_server.account_manager.capital = 100
        self.order_book.current_price = Mock(return_value=150)
        self.portfolio_server.account.full_init_margin_req = 1000
        self.portfolio_server.account.full_available_funds = 100
        self.manager._set_order = MagicMock()
        self.order_book.retrieve = Mock(return_value=10)  # current price

        # Test Order set b/c no funds currently available
        self.manager._handle_signal(self.timestamp, self.trade_instructions)

        # Validate
        self.assertTrue(self.manager._set_order.call_count == 0)

    def test_handle_event_valid(self):
        self.portfolio_server.get_active_order_tickers = Mock(
            return_value=[1, 2]
        )
        self.manager._handle_signal = MagicMock()

        # Test handle_signal called
        self.manager.handle_event(self.signal_event)

        # Validate
        self.assertEqual(self.manager._handle_signal.call_count, 0)

    def test_handle_event_without_active_orders(self):
        self.portfolio_server.get_active_order_tickers = Mock(return_value=[])
        self.manager._handle_signal = MagicMock()

        # Test
        self.manager._handle_signal(self.signal_event)

        # Validate
        self.manager._handle_signal.assert_called_once()

    def test_set_order(self):
        timestamp = 1651500000
        action = Action.LONG
        trade_id = 2
        leg_id = 6
        order = MarketOrder(action=action, quantity=10)
        contract = Contract()
        self.bus.publish = MagicMock()

        order_event = OrderEvent(
            timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            action=action,
            contract=contract,
            order=order,
        )

        # Test
        self.manager._set_order(
            timestamp=timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            action=action,
            order=order,
            contract=contract,
        )

        # Validation
        self.assertEqual(self.bus.publish.call_count, 1)
        args = self.bus.publish.call_args[0]

        self.assertEqual(args[0], EventType.ORDER)
        self.assertEqual(args[1], order_event)


if __name__ == "__main__":
    unittest.main()
