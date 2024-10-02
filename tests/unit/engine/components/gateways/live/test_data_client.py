import unittest
from ibapi.contract import Contract
from unittest.mock import Mock, patch, MagicMock
from midas.engine.components.gateways.live.data_client import DataClient
from datetime import time
from midas.utils.logger import SystemLogger
from midas.engine.config import LiveDataType
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


class TestDataClient(unittest.TestCase):
    def setUp(self):
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

        # Mock Config
        self.config = Mock(
            strategy_parameters={"tick_interval": 5},
            data_source={
                "host": 1,
                "port": 2,
                "client_id": 0,
                "account_id": "1234",
            },
        )

        # DataClient instance
        self.data_client = DataClient(self.config, self.symbols_map)

        # Mock data wrapper
        self.data_client.app = Mock(tick_data={})
        self.data_client.app.reqId_to_instrument = {}

    # Basic Validation
    def test_get_valid_id(self):
        # Mock next valid id
        id = 10
        self.data_client.app.next_valid_order_id = id

        # Test
        current_id = self.data_client._get_valid_id()

        # Validate
        self.assertEqual(current_id, id)
        self.assertEqual(self.data_client.app.next_valid_order_id, id + 1)

    def test_is_connected(self):
        # Test
        self.data_client.app.isConnected.return_value = True

        # Validate
        self.assertTrue(self.data_client.is_connected())
        self.data_client.app.isConnected.assert_called_once()

    def test_connect(self):
        # Ensure connect method starts a thread and waits for connection events
        with patch(
            "threading.Thread.start", return_value=None
        ) as mock_thread_start:
            # Test
            self.data_client.connect()

            # Validate
            mock_thread_start.assert_called_once()
            self.data_client.app.connected_event.wait.assert_called_once()
            self.data_client.app.valid_id_event.wait.assert_called_once()

    def test_disconnect(self):
        # Test
        self.data_client.disconnect()

        # Validate
        self.data_client.app.disconnect.assert_called_once()

    def test_get_data_bar(self):
        contract = Contract()
        data_type = LiveDataType.BAR

        with patch.object(
            self.data_client, "stream_5_sec_bars"
        ) as mock_method:
            # Test
            self.data_client.get_data(data_type, contract)

            # Validate
            mock_method.assert_called_once_with(contract)

    def test_get_data_quote(self):
        contract = Contract()
        data_type = LiveDataType.TICK

        with patch.object(
            self.data_client, "stream_quote_data"
        ) as mock_method:
            # Test
            self.data_client.get_data(data_type, contract)

            # Validate
            mock_method.assert_called_once_with(contract)

    def test_stream_5_sec_bars(self):
        contract = Contract()
        contract.symbol = "AAPL"

        with patch.object(
            self.data_client, "_get_valid_id", return_value=123
        ) as _:
            # Test
            self.data_client.stream_5_sec_bars(contract=contract)

            # Validate
            self.data_client.app.reqRealTimeBars.assert_called_once_with(
                reqId=123,
                contract=contract,
                barSize=5,
                whatToShow="TRADES",
                useRTH=False,
                realTimeBarsOptions=[],
            )
            self.assertEqual(
                self.data_client.app.reqId_to_instrument[123],
                self.symbols_map.get_id(contract.symbol),
            )

    def test_stream_5_sec_bars_already_streaming(self):
        contract = Contract()
        contract.symbol = "AAPL"
        self.data_client.app.reqId_to_instrument = {
            321: self.symbols_map.get_id(contract.symbol)
        }

        with patch.object(
            self.data_client, "_get_valid_id", return_value=123
        ) as _:
            # Test
            self.data_client.stream_5_sec_bars(contract=contract)

            # Validate
            self.assertFalse(self.data_client.app.reqRealTimeBars.called)

    def test_stream_quote_data(self):
        contract = Contract()
        contract.symbol = "AAPL"

        with patch.object(
            self.data_client, "_get_valid_id", return_value=123
        ) as _:
            # Test
            self.data_client.stream_quote_data(contract=contract)

            # Validate
            self.data_client.app.reqMktData.assert_called_once_with(
                reqId=123,
                contract=contract,
                genericTickList="",
                snapshot=False,
                regulatorySnapshot=False,
                mktDataOptions=[],
            )
            self.assertEqual(
                self.data_client.app.reqId_to_instrument[123],
                self.symbols_map.get_id(contract.symbol),
            )

    def test_stream_quote_data_already_streaming(self):
        contract = Contract()
        contract.symbol = "AAPL"
        self.data_client.app.reqId_to_instrument = {321: contract.symbol}

        with patch.object(
            self.data_client, "_get_valid_id", return_value=123
        ) as _:
            # Test
            self.data_client.stream_quote_data(contract=contract)

            # Validate
            self.assertFalse(self.data_client.app.reqRealTimeBars.called)

    def test_cancel_all_bar_data(self):
        contract = Contract()
        contract.symbol = "AAPL"
        self.data_client.app.reqId_to_instrument = {321: contract.symbol}

        # Test
        self.data_client.cancel_all_bar_data()

        # Validate
        self.assertEqual(self.data_client.app.reqId_to_instrument, {})

    def test_cancel_all_quote_data(self):
        contract = Contract()
        contract.symbol = "AAPL"
        self.data_client.app.reqId_to_instrument = {321: contract.symbol}

        # Test
        self.data_client.cancel_all_quote_data()

        # Validate
        self.assertEqual(self.data_client.app.reqId_to_instrument, {})

    # Type Validation
    def test_get_data_value_error(self):
        contract = Contract()
        data_type = "BAR"

        with self.assertRaisesRegex(
            ValueError, "'data_type' must be of type MarketDataType enum."
        ):
            self.data_client.get_data(data_type, contract)


if __name__ == "__main__":
    unittest.main()
