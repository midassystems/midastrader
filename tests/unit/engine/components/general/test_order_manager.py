import unittest
from datetime import time
from unittest.mock import Mock, MagicMock
from ibapi.contract import Contract
from midas.account import Account
from midas.signal import SignalInstruction
from midas.engine.components.order_manager import OrderExecutionManager
from midas.utils.logger import SystemLogger
from midas.engine.events import SignalEvent, OrderEvent
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
from midas.orders import MarketOrder, LimitOrder, StopLoss, OrderType, Action
from midas.symbol import SymbolMap
from midas.engine.components.observer.base import EventType


class TestOrderManager(unittest.TestCase):
    def setUp(self) -> None:
        # Mock methods
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()

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

        # Test account
        self.mock_portfolio_server.account = Account(
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
        self.order_manager = OrderExecutionManager(
            self.symbols_map,
            self.mock_order_book,
            self.mock_portfolio_server,
        )

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
    def test_create_marketorder_valid(self):
        trade_instructions = self.trade_equity

        # Test
        order = self.order_manager._create_order(trade_instructions)

        # Validation
        self.assertEqual(type(order), MarketOrder)
        self.assertEqual(
            order.order.action, trade_instructions.action.to_broker_standard()
        )
        self.assertEqual(
            order.order.totalQuantity, abs(trade_instructions.quantity)
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

        # Test
        order = self.order_manager._create_order(trade_instructions)

        # Validation
        self.assertEqual(type(order), LimitOrder)
        self.assertEqual(
            order.order.action, trade_instructions.action.to_broker_standard()
        )
        self.assertEqual(
            order.order.totalQuantity, abs(trade_instructions.quantity)
        )
        self.assertEqual(order.order.lmtPrice, trade_instructions.limit_price)

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

        # Test
        order = self.order_manager._create_order(trade_instructions)

        # Validation
        self.assertEqual(type(order), StopLoss)
        self.assertEqual(
            order.order.action, trade_instructions.action.to_broker_standard()
        )
        self.assertEqual(
            order.order.totalQuantity, abs(trade_instructions.quantity)
        )
        self.assertEqual(order.order.auxPrice, trade_instructions.aux_price)

    def test_handle_signal_sufficient_captial(self):
        self.mock_portfolio_server.capital = 10000
        self.mock_order_book.current_price.return_value = 150
        self.mock_portfolio_server.account.full_init_margin_req = 1000
        self.mock_portfolio_server.account.full_available_funds = 50000
        self.order_manager._set_order = MagicMock()
        self.mock_order_book.retrieve.return_value = 10  # current price

        # Test Order Set b/c funds available
        self.order_manager._handle_signal(
            timestamp=self.timestamp,
            trade_instructions=self.trade_instructions,
        )

        # Validate
        self.assertTrue(self.order_manager._set_order.call_count > 0)

    def test_handle_signal_insufficient_capital(self):
        self.mock_portfolio_server.capital = 100
        self.mock_order_book.current_price.return_value = 150
        self.mock_portfolio_server.account.full_init_margin_req = 1000
        self.mock_portfolio_server.account.full_available_funds = 100
        self.order_manager._set_order = MagicMock()
        self.mock_order_book.retrieve.return_value = 10

        # Test Order set b/c no funds currently available
        self.order_manager._handle_signal(
            timestamp=self.timestamp,
            trade_instructions=self.trade_instructions,
        )

        # Validate
        self.assertTrue(self.order_manager._set_order.call_count == 0)

    def test_handle_event_valid(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = [
            1,
            2,
        ]
        self.order_manager._handle_signal = MagicMock()

        # Test handle_signal called
        self.order_manager.handle_event(
            Mock(),
            EventType.SIGNAL,
            self.signal_event,
        )
        self.assertEqual(self.order_manager._handle_signal.call_count, 0)

    def test_handle_event_without_active_orders(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = []
        self.order_manager._handle_signal = MagicMock()

        # Test
        self.order_manager._handle_signal(
            Mock(),
            EventType.SIGNAL,
            self.signal_event,
        )

        # Validate
        self.order_manager._handle_signal.assert_called_once()

    def test_set_order(self):
        self.timestamp = 1651500000
        self.action = Action.LONG
        self.trade_id = 2
        self.leg_id = 6
        self.order = MarketOrder(action=self.action, quantity=10)
        self.contract = Contract()
        self.order_manager.notify = MagicMock()

        # Test
        self.order_manager._set_order(
            timestamp=self.timestamp,
            action=self.action,
            trade_id=self.trade_id,
            leg_id=self.leg_id,
            order=self.order,
            contract=self.contract,
        )

        # Validation
        args = self.order_manager.notify.call_args[0]
        self.assertEqual(EventType.ORDER_CREATED, args[0])
        self.assertIsInstance(args[1], OrderEvent)


if __name__ == "__main__":
    unittest.main()
