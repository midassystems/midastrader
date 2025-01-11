import unittest
import threading
from time import sleep
from datetime import datetime, time
from unittest.mock import Mock, MagicMock
from mbn import OhlcvMsg

from midastrader.config import LiveDataType, Parameters, Mode
from midastrader.structs.events import EODEvent
from midastrader.message_bus import MessageBus, EventType
from midastrader.utils.logger import SystemLogger
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.unix import unix_to_iso
from midastrader.data.adaptors.historical import HistoricalAdaptor
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


class TestHistoricalAdaptor(unittest.TestCase):
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
        self.symbols = [hogs, aapl]

        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(hogs)
        self.symbols_map.add_symbol(aapl)

        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # Dataclient instance
        self.bus = MessageBus()

        kwargs = {"data_file": "tests/unit/hogs_corn_ohlcv1h.bin"}
        self.adaptor = HistoricalAdaptor(
            self.symbols_map,
            self.bus,
            **kwargs,
        )

    # Basic Validation
    def test_get_data_file(self):
        # Parameters
        params = Parameters(
            strategy_name="Testing",
            capital=10000000,
            schema="Ohlcv-1d",
            data_type=LiveDataType.BAR,
            start="2024-10-01",
            end="2024-10-05",
            risk_free_rate=0.9,
            symbols=self.symbols,
        )

        kwargs = {"data_file": "tests/unit/hogs_corn_ohlcv1h.bin"}
        adaptor = HistoricalAdaptor(self.symbols_map, self.bus, **kwargs)

        # Test
        response = adaptor.get_data(params)

        # Validate
        self.assertTrue(response)

    def test_get_data_database(self):

        # Parameters
        params = Parameters(
            strategy_name="Testing",
            capital=10000000,
            schema="Ohlcv-1d",
            data_type=LiveDataType.BAR,
            start="2024-10-01",
            end="2024-10-05",
            risk_free_rate=0.9,
            symbols=self.symbols,
        )

        kwargs = {"data_file": ""}
        adaptor = HistoricalAdaptor(self.symbols_map, self.bus, **kwargs)
        adaptor.database_client.historical.get_records = Mock()

        # Test
        _ = adaptor.get_data(params)

        # Validate
        self.assertTrue(adaptor.database_client.historical.get_records.called)

    def test_process_exit(self):
        self.adaptor.data_stream = MagicMock()
        self.adaptor.cleanup = Mock()

        # Test
        threading.Thread(target=self.adaptor.process, daemon=True).start()
        self.adaptor.shutdown_event.set()
        sleep(1)

        # Validate
        self.assertTrue(self.adaptor.cleanup.called)

    def test_check_eod(self):
        bar = OhlcvMsg(
            instrument_id=1,
            ts_event=1727916834000000000,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        event = EODEvent(timestamp=datetime(2024, 10, 2).date())

        # Test
        self.bus.publish = MagicMock()
        self.adaptor._await_data_processed = MagicMock()
        self.adaptor._check_eod(bar)

        # Validate
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.DATA)
        self.assertEqual(args[1], event)
        self.assertTrue(self.adaptor._await_data_processed.called)

    def test_check_eod_not(self):
        bar = OhlcvMsg(
            instrument_id=1,
            ts_event=1727888034000000000,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        # Test
        ts = datetime.fromisoformat(
            unix_to_iso(bar.ts_event, tz_info="America/New_York")
        )
        date = ts.date()

        self.adaptor.current_date = date
        self.bus.publish = MagicMock()
        self.adaptor._check_eod(bar)

        # Validate
        self.assertEqual(self.bus.publish.call_count, 0)

    def test_data_stream(self):
        self.adaptor.data = Mock()
        record = OhlcvMsg(
            instrument_id=1,
            ts_event=1707221160000000000,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )
        self.adaptor.data.replay.return_value = record
        self.adaptor.data.metadata.mappings.get_ticker.return_value = "HE.n.0"
        self.adaptor.mode = Mode.BACKTEST

        # Test
        self.adaptor._check_eod = Mock()
        self.bus.publish = MagicMock()
        result = self.adaptor.data_stream()

        # Validate
        self.assertTrue(result)
        self.assertTrue(self.adaptor._check_eod.called)
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.DATA)
        self.assertEqual(args[1], record)


if __name__ == "__main__":
    unittest.main()
