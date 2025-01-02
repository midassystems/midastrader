import unittest
from time import sleep
from datetime import time
import threading
from ibapi.contract import Contract
from unittest.mock import MagicMock


from midas.message_bus import MessageBus, EventType
from midas.structs.orders import Action, MarketOrder
from midas.structs.symbol import SymbolMap
from midas.utils.logger import SystemLogger
from midas.execution.adaptors.dummy.broker_client import DummyAdaptor
from midas.structs.events import OrderEvent
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


class TestDummyAdaptor(unittest.TestCase):
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

        # BrokerClient instance
        self.bus = MessageBus()
        self.adaptor = DummyAdaptor(self.symbols_map, self.bus, 100000)
        self.adaptor.broker = MagicMock()

    # Basic Validation
    def test_process_orders(self):
        # Mock order
        timestamp = 1651500000
        action = Action.LONG
        trade_id = 2
        leg_id = 6
        order = MarketOrder(action, 10)
        contract = Contract()

        event = OrderEvent(
            timestamp=timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            action=action,
            order=order,
            contract=contract,
        )

        # Test
        threading.Thread(target=self.adaptor.process, daemon=True).start()
        self.bus.publish(EventType.ORDER, event)
        sleep(1)

        # Validate
        self.assertEqual(self.bus.topics[EventType.TRADE].get(), event)

    # def test_handle_event_order(self):
    #     # Test
    #     self.broker_client.handle_order = Mock()
    #     self.broker_client.handle_event(Mock(), EventType.ORDER_CREATED, event)
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.handle_order.call_count, 1)
    #
    # # Basic Validation
    # def test_handle_event_trade(self):
    #     # Trade details
    #     timestamp = 641651500000
    #     trade_id = 1
    #     leg_id = 2
    #     contract = Contract()
    #     contract.symbol = "AAPL"
    #     quantity = -10
    #     action = Action.LONG
    #     fill_price = 9.9
    #     fees = 90.9
    #     instrument = self.symbols_map.get_id(contract.symbol)
    #
    #     # Execution dict
    #     valid_trade = Trade(
    #         timestamp=timestamp,
    #         trade_id=trade_id,
    #         leg_id=leg_id,
    #         instrument=instrument,
    #         quantity=round(quantity, 4),
    #         avg_price=fill_price,
    #         trade_value=round(fill_price * quantity, 2),
    #         trade_cost=round(fill_price * quantity, 2),
    #         action=action.value,
    #         fees=round(fees, 4),
    #     )
    #     self.valid_contract = Contract()
    #     self.valid_order = Order()
    #
    #     # Executiom event
    #     event = ExecutionEvent(
    #         timestamp=timestamp,
    #         trade_details=valid_trade,
    #         action=action,
    #         contract=contract,
    #     )
    #
    #     # Test
    #     self.broker_client.handle_execution = Mock()
    #     self.broker_client.handle_event(
    #         Mock(),
    #         EventType.TRADE_EXECUTED,
    #         event,
    #     )
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.handle_execution.call_count, 1)
    #
    # # Basic Validation
    # def test_handle_event_eod(self):
    #     event = EODEvent(datetime(2024, 10, 1))
    #
    #     # Test
    #     self.broker_client.handle_eod = Mock()
    #     self.broker_client.handle_event(
    #         Mock(),
    #         EventType.EOD_EVENT,
    #         event,
    #     )
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.handle_eod.call_count, 1)
    #
    # # Basic Validation
    # def test_handle_event_order_book(self):
    #     bar = OhlcvMsg(
    #         instrument_id=1,
    #         ts_event=12345432,
    #         open=int(80.90 * 1e9),
    #         close=int(9000.90 * 1e9),
    #         high=int(75.90 * 1e9),
    #         low=int(8800.09 * 1e9),
    #         volume=880000,
    #     )
    #
    #     event = MarketEvent(123454323, bar)
    #
    #     # Test
    #     self.broker_client.update_equity_value = Mock()
    #     self.broker_client.handle_event(
    #         Mock(),
    #         EventType.ORDER_BOOK,
    #         event,
    #     )
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.update_equity_value.call_count, 1)
    #
    # def test_handle_order(self):
    #     # Order data
    #     self.valid_timestamp = 1651500000
    #     self.valid_action = Action.LONG
    #     self.valid_trade_id = 2
    #     self.valid_leg_id = 6
    #     self.valid_order = MarketOrder(self.valid_action, 10)
    #     self.valid_contract = Contract()
    #
    #     # Order event
    #     event = OrderEvent(
    #         timestamp=self.valid_timestamp,
    #         trade_id=self.valid_trade_id,
    #         leg_id=self.valid_leg_id,
    #         action=self.valid_action,
    #         order=self.valid_order,
    #         contract=self.valid_contract,
    #     )
    #
    #     # Test
    #     self.dummy_broker.placeOrder = Mock()
    #     self.broker_client.handle_order(event)
    #
    #     # Validate
    #     self.assertEqual(self.dummy_broker.placeOrder.call_count, 1)
    #
    # def test_update_positions(self):
    #     # Position data
    #     ticker = "HEJ4"
    #     contract = Contract()
    #     contract.symbol = ticker
    #
    #     # Position object
    #     valid_position = EquityPosition(
    #         action="BUY",
    #         avg_price=10.90,
    #         quantity=100,
    #         quantity_multiplier=1,
    #         price_multiplier=1,
    #         market_price=12,
    #     )
    #     self.dummy_broker.return_positions.return_value = {
    #         contract: valid_position
    #     }
    #
    #     # Test
    #     self.broker_client.notify = Mock()
    #     self.broker_client.update_positions()
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.notify.call_count, 1)
    #
    # def test_update_trades(self):
    #     # Trade data
    #     aapl_contract = Contract()
    #     aapl_contract.symbol = "AAPL"
    #     aapl_contract.secType = "STK"
    #     aapl_action = Action.LONG
    #     aapl_quantity = 10
    #     aapl_entry_price = 50
    #     instrument = self.symbols_map.get_id(aapl_contract.symbol)
    #
    #     # Execution details
    #     valid_trade_appl = Trade(
    #         timestamp=165000000,
    #         trade_id=1,
    #         leg_id=1,
    #         instrument=instrument,
    #         quantity=round(aapl_quantity, 4),
    #         avg_price=aapl_entry_price,
    #         trade_value=round(aapl_entry_price * aapl_quantity, 2),
    #         trade_cost=round(aapl_entry_price * aapl_quantity, 2),
    #         action=aapl_action.value,
    #         fees=70,
    #     )
    #
    #     # Mock response
    #     self.broker_client.notify = Mock()
    #     self.dummy_broker.return_executed_trades.return_value = {
    #         aapl_contract: valid_trade_appl
    #     }
    #
    #     # Test
    #     self.broker_client.update_trades()
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.notify.call_count, 1)
    #
    # def test_update_account(self):
    #     # Account object
    #     account = Account(
    #         timestamp=1704214800000000000,
    #         full_available_funds=502398.7799999999,
    #         full_init_margin_req=497474.57,
    #         net_liquidation=999873.3499999999,
    #         unrealized_pnl=1234,
    #         full_maint_margin_req=12345,
    #         excess_liquidity=9876543,
    #         currency="USD",
    #         buying_power=765432,
    #         futures_pnl=76543,
    #         total_cash_balance=4321,
    #     )
    #
    #     # Mock dummy broker response
    #     self.dummy_broker.return_account.return_value = account
    #
    #     # Test
    #     self.broker_client.notify = Mock()
    #     self.broker_client.update_account()
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.notify.call_count, 1)
    #
    # def test_update_equity_value(self):
    #     # Equity details dict
    #     equity = EquityDetails(timestamp=123456, equity_value=100000)
    #     self.dummy_broker.return_equity_value.return_value = equity
    #
    #     # Test
    #     self.broker_client._update_account = Mock()
    #     self.broker_client.notify = Mock()
    #     self.broker_client.update_equity_value()
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.notify.call_count, 1)
    #
    # def test_handle_execution(self):
    #     # Trade details
    #     timestamp = 641651500000
    #     trade_id = 1
    #     leg_id = 2
    #     contract = Contract()
    #     contract.symbol = "AAPL"
    #     quantity = -10
    #     action = Action.LONG
    #     fill_price = 9.9
    #     fees = 90.9
    #     instrument = self.symbols_map.get_id(contract.symbol)
    #
    #     # Execution dict
    #     valid_trade = Trade(
    #         timestamp=timestamp,
    #         trade_id=trade_id,
    #         leg_id=leg_id,
    #         instrument=instrument,
    #         quantity=round(quantity, 4),
    #         avg_price=fill_price,
    #         trade_value=round(fill_price * quantity, 2),
    #         trade_cost=round(fill_price * quantity, 2),
    #         action=action.value,
    #         fees=round(fees, 4),
    #     )
    #     self.valid_contract = Contract()
    #     self.valid_order = Order()
    #
    #     # Executiom event
    #     exec = ExecutionEvent(
    #         timestamp=timestamp,
    #         trade_details=valid_trade,
    #         action=action,
    #         contract=contract,
    #     )
    #
    #     # Mock last trade
    #     self.broker_client.update_positions = Mock()
    #     self.broker_client.update_account = Mock()
    #     self.broker_client.update_equity_value = Mock()
    #     self.broker_client.update_trades = Mock()
    #     self.broker_client.broker.last_trade = valid_trade
    #
    #     # Test
    #     self.broker_client.handle_execution(exec)
    #
    #     # Validate
    #     self.assertEqual(self.broker_client.update_positions.call_count, 1)
    #     self.assertEqual(self.broker_client.update_account.call_count, 1)
    #     self.assertEqual(self.broker_client.update_equity_value.call_count, 1)
    #     self.assertEqual(self.broker_client.update_trades.call_count, 1)


if __name__ == "__main__":
    unittest.main()
