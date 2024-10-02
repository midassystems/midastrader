import unittest
from midas.utils.logger import SystemLogger
from datetime import time
from unittest.mock import Mock, MagicMock
from midas.engine.events import MarketEvent
from midas.engine.components.order_book import OrderBook
from midas.engine.components.observer import EventType
from mbn import OhlcvMsg, BboMsg, Side, BidAskPair
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
from midas.symbol import SymbolMap


class TestOrderBook(unittest.TestCase):
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
        self.order_book = OrderBook(self.symbols_map)
        self.timestamp = 1707221160000000000

        self.bar = OhlcvMsg(
            instrument_id=1,
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
    def test_handle_event_bar(self):
        market_event = MarketEvent(self.timestamp, self.bar)
        self.order_book.notify = Mock()

        # Test
        self.order_book.handle_event(Mock(), EventType.MARKET_DATA, self.bar)

        # Validate
        args = self.order_book.notify.call_args[0]
        self.assertEqual(
            self.order_book.book, {self.bar.instrument_id: self.bar}
        )
        self.assertEqual(args[0], EventType.ORDER_BOOK)
        self.assertEqual(args[1], market_event)

    def test_handle_event_tick(self):
        market_event = MarketEvent(self.timestamp, self.tick)
        self.order_book.notify = Mock()

        # Test
        self.order_book.handle_event(
            Mock(),
            EventType.MARKET_DATA,
            self.tick,
        )

        # Validate
        args = self.order_book.notify.call_args[0]
        self.assertEqual(
            self.order_book.book, {self.tick.instrument_id: self.tick}
        )
        self.assertEqual(args[0], EventType.ORDER_BOOK)
        self.assertEqual(args[1], market_event)

    def test_retrieve(self):
        self.order_book.book = {
            self.bar.instrument_id: self.bar,
            self.tick.instrument_id: self.tick,
        }

        # Test
        self.assertEqual(self.order_book.retrieve(1), self.bar)
        self.assertEqual(self.order_book.retrieve(2), self.tick)

    def test_retrieve_all(self):
        book = {
            self.bar.instrument_id: self.bar,
            self.tick.instrument_id: self.tick,
        }

        self.order_book.book = book

        # Test
        result = self.order_book.retrieve_all()

        # Validate
        self.assertEqual(result, book)


if __name__ == "__main__":
    unittest.main()
