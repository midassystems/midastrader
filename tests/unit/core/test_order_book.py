import unittest
from time import sleep
import threading
from datetime import time
from midastrader.utils.logger import SystemLogger
from mbn import OhlcvMsg, BboMsg, Side, BidAskPair
from unittest.mock import MagicMock

from midastrader.config import Mode
from midastrader.structs.events import MarketEvent
from midastrader.core.adapters.order_book import OrderBook, OrderBookManager
from midastrader.message_bus import MessageBus, EventType
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
from midastrader.structs.symbol import SymbolMap


class TestOrderBook(unittest.TestCase):
    def setUp(self) -> None:
        self.book = OrderBook.get_instance()

        self.timestamp = 1707221160000000000
        self.bar = OhlcvMsg(
            instrument_id=1,
            rollover_flag=0,
            ts_event=self.timestamp,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        self.bar2 = OhlcvMsg(
            instrument_id=1,
            rollover_flag=0,
            ts_event=self.timestamp,
            open=int(90.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        self.tick = BboMsg(
            instrument_id=2,
            rollover_flag=0,
            ts_event=self.timestamp,
            price=int(12 * 1e9),
            size=12345,
            side=Side.NONE,
            flags=0,
            ts_recv=123456776543,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=11,
                    ask_px=23,
                    bid_sz=123,
                    ask_sz=234,
                    bid_ct=3,
                    ask_ct=4,
                )
            ],
        )

    # Basic Validation
    def test_update_empty(self):
        self.book._book = {}  # enusre empty

        # Test
        self.book._update(self.bar)

        # Validate
        val = self.book._book.get(1)
        self.assertEqual(val, self.bar)

    def test_update_not_empty(self):
        self.book._book = {}  # enusre empty

        # Test
        self.book._update(self.bar)
        self.book._update(self.bar2)

        # Validate
        val = self.book._book.get(1)
        self.assertEqual(val, self.bar2)
        self.assertEqual(len(self.book._book.keys()), 1)

    def test_retrieve(self):
        self.book._book = {
            self.bar.instrument_id: self.bar,
            self.tick.instrument_id: self.tick,
        }

        # Test
        self.assertEqual(self.book.retrieve(1), self.bar)
        self.assertEqual(self.book.retrieve(2), self.tick)

    def test_retrieve_all(self):
        book = {
            self.bar.instrument_id: self.bar,
            self.tick.instrument_id: self.tick,
        }

        self.book._book = book

        # Test
        result = self.book.retrieve_all()

        # Validate
        self.assertEqual(result, book)


class TestOrderBookManager(unittest.TestCase):
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

        # Bar orderbook
        self.bus = MessageBus()
        self.manager = OrderBookManager(
            self.symbols_map,
            self.bus,
            Mode.BACKTEST,
        )
        self.book = OrderBook.get_instance()
        threading.Thread(target=self.manager.process, daemon=True).start()

        self.timestamp = 1707221160000000000
        self.bar = OhlcvMsg(
            instrument_id=1,
            rollover_flag=0,
            ts_event=self.timestamp,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        self.tick = BboMsg(
            instrument_id=2,
            ts_event=self.timestamp,
            rollover_flag=0,
            price=int(12 * 1e9),
            size=12345,
            side=Side.NONE,
            flags=0,
            ts_recv=123456776543,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=11,
                    ask_px=23,
                    bid_sz=123,
                    ask_sz=234,
                    bid_ct=3,
                    ask_ct=4,
                )
            ],
        )

    # Basic Validation
    def test_process(self):
        self.manager.handle_record = MagicMock()

        # Test
        self.bus.publish(EventType.DATA, self.bar)
        sleep(1)

        # Validate
        args = self.manager.handle_record.call_args[0]
        self.assertEqual(self.bar, args[0])

    def test_handle_event_bar(self):
        market_event = MarketEvent(self.timestamp, self.bar)
        self.bus.publish = MagicMock()

        # Test
        self.manager.handle_record(self.bar)
        sleep(1)

        # Validate
        record = self.book.retrieve(1)
        self.assertEqual(record, self.bar)

        self.assertEqual(self.bus.publish.call_count, 3)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.UPDATE_EQUITY)
        self.assertEqual(first_call_args[1], True)

        # Validate the second call
        second_call_args = calls[1][0]
        self.assertEqual(second_call_args[0], EventType.UPDATE_SYSTEM)
        self.assertEqual(second_call_args[1], True)

        third_call_args = calls[2][0]
        self.assertEqual(third_call_args[0], EventType.ORDER_BOOK)
        self.assertEqual(third_call_args[1], market_event)

    def test_handle_event_tick(self):
        market_event = MarketEvent(self.timestamp, self.tick)
        self.bus.publish = MagicMock()

        # Test
        self.manager.handle_record(self.tick)
        sleep(1)

        # Validate
        record = self.book.retrieve(2)
        self.assertEqual(record, self.tick)

        self.assertEqual(self.bus.publish.call_count, 3)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.UPDATE_EQUITY)
        self.assertEqual(first_call_args[1], True)

        # Validate the second call
        second_call_args = calls[1][0]
        self.assertEqual(second_call_args[0], EventType.UPDATE_SYSTEM)
        self.assertEqual(second_call_args[1], True)

        third_call_args = calls[2][0]
        self.assertEqual(third_call_args[0], EventType.ORDER_BOOK)
        self.assertEqual(third_call_args[1], market_event)


if __name__ == "__main__":
    unittest.main()
