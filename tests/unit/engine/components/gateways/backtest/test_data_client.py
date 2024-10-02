import unittest
from midas.engine.components.observer.base import EventType
from midas.engine.events import EODEvent
from midas.utils.logger import SystemLogger
from datetime import datetime, time
from unittest.mock import Mock, MagicMock
from mbn import OhlcvMsg, Schema, BufferStore
from midas.symbol import SymbolMap
from midas.engine.components.gateways.backtest.data_client import DataClient
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


class TestDataClient(unittest.TestCase):
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

        # Mock objects
        self.db_client = Mock()

        # Dataclient instance
        self.data_client = DataClient(self.db_client, self.symbols_map)

    # Basic Validation
    def test_load_backtest_data(self):
        tickers = ["AAPL", "TSLA"]
        start_date = "2024-01-01"
        end_date = "2024-12-12"
        schema = Schema.OHLCV1_S

        # Test
        self.data_client.get_data = Mock()
        self.data_client.load_backtest_data(
            tickers,
            start_date,
            end_date,
            schema,
        )

        # Validate
        self.assertTrue(self.data_client.get_data.called)

    def test_get_data_file(self):
        tickers = ["AAPL", "TSLA"]
        start_date = "2024-01-01"
        end_date = "2024-12-12"
        schema = Schema.OHLCV1_S
        data_file = "tests/unit/engine/hogs_corn_ohlcv1h.bin"

        # Test
        data = self.data_client.get_data(
            tickers,
            start_date,
            end_date,
            schema,
            data_file,
        )

        # Validate
        self.assertIsInstance(data, BufferStore)

    def test_get_data_database(self):
        tickers = ["AAPL", "TSLA"]
        start_date = "2024-01-01"
        end_date = "2024-12-12"
        schema = Schema.OHLCV1_S

        # Test
        self.db_client.get_records = Mock()
        _ = self.data_client.get_data(
            tickers,
            start_date,
            end_date,
            schema,
        )

        # Validate
        self.assertTrue(self.db_client.get_records.called)

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
        self.data_client.notify = Mock()
        self.data_client._check_eod(bar)

        # Validate
        args = self.data_client.notify.call_args[0]
        self.assertEqual(args[0], EventType.EOD_EVENT)
        self.assertEqual(args[1], event)
        self.assertTrue(self.data_client.notify.called)

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
        self.data_client.notify = Mock()
        self.data_client._check_eod(bar)

        # Validate
        self.assertEqual(self.data_client.notify.call_count, 0)

    def test_data_stream(self):
        self.data_client.data = Mock()

        self.data_client.data.replay.return_value = OhlcvMsg(
            instrument_id=1,
            ts_event=1707221160000000000,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )
        self.data_client.data.metadata.mappings.get_ticker.return_value = (
            "HE.n.0"
        )
        # Test
        self.data_client._check_eod = Mock()
        self.data_client.notify = Mock()
        result = self.data_client.data_stream()

        # Validate
        self.assertTrue(result)
        self.assertTrue(self.data_client._check_eod.called)
        self.assertTrue(self.data_client.notify.called)


if __name__ == "__main__":
    unittest.main()
