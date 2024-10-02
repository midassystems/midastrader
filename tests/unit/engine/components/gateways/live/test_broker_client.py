import unittest
from ibapi.contract import Contract
from datetime import time
from unittest.mock import Mock, patch, MagicMock
from midas.engine.events import OrderEvent
from midas.orders import Action, MarketOrder
from midas.engine.components.gateways.live.broker_client import BrokerClient
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import EventType
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


class TestBrokerClient(unittest.TestCase):
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
            broker={
                "host": 1,
                "port": 2,
                "client_id": 0,
                "account_id": "1234",
            },
        )

        # BrokerClient instance
        self.broker_client = BrokerClient(self.config, self.symbols_map)
        self.broker_client.app = Mock()

    # Basic Validation
    def test_get_valid_id(self):
        # Set next validId
        id = 10
        self.broker_client.app.next_valid_order_id = id

        # Test
        current_id = self.broker_client._get_valid_id()

        # Validate
        self.assertEqual(current_id, id)
        self.assertEqual(self.broker_client.app.next_valid_order_id, id + 1)

    def test_is_connected(self):
        # Test
        self.broker_client.app.isConnected.return_value = True

        # Validate
        self.assertTrue(self.broker_client.is_connected())
        self.broker_client.app.isConnected.assert_called_once()

    def test_connect(self):
        # Ensure connect method starts a thread and waits for connection events
        with patch(
            "threading.Thread.start", return_value=None
        ) as mock_thread_start:
            # Test
            self.broker_client.connect()

            # Validate
            mock_thread_start.assert_called_once()
            self.broker_client.app.connected_event.wait.assert_called_once()
            self.broker_client.app.valid_id_event.wait.assert_called_once()

    def test_disconnect(self):
        # Test
        self.broker_client.disconnect()

        # Validate
        self.broker_client.app.disconnect.assert_called_once()

    def test_handle_event_valid(self):
        # Mock order event
        self.valid_timestamp = 1651500000
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id = 6
        self.valid_order = MarketOrder(action=self.valid_action, quantity=10)
        self.valid_contract = Contract()

        event = OrderEvent(
            timestamp=self.valid_timestamp,
            trade_id=self.valid_trade_id,
            leg_id=self.valid_leg_id,
            action=self.valid_action,
            order=self.valid_order,
            contract=self.valid_contract,
        )

        # Test
        self.broker_client.handle_order = Mock()
        self.broker_client.handle_event(Mock(), EventType.ORDER_CREATED, event)

        # Validate
        self.assertEqual(self.broker_client.handle_order.call_count, 1)

    def test_handle_order(self):
        # Mock order event
        self.valid_timestamp = 1651500000
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id = 6
        self.valid_order = MarketOrder(action=self.valid_action, quantity=10)
        self.valid_contract = Contract()

        event = OrderEvent(
            timestamp=self.valid_timestamp,
            trade_id=self.valid_trade_id,
            leg_id=self.valid_leg_id,
            action=self.valid_action,
            order=self.valid_order,
            contract=self.valid_contract,
        )

        # Test
        self.broker_client._get_valid_id = Mock(return_value=1)
        self.broker_client.app.placeOrder = Mock()
        self.broker_client.handle_order(event)

        # Validate
        self.assertEqual(self.broker_client.app.placeOrder.call_count, 1)

    def test_request_account_summary(self):
        self.broker_client._get_valid_id = Mock(return_value=10)
        expected_tags_string = "Timestamp,FullAvailableFunds,FullInitMarginReq,NetLiquidation,UnrealizedPnL,FullMaintMarginReq,ExcessLiquidity,Currency,BuyingPower,FuturesPNL,TotalCashBalance"

        with patch.object(
            self.broker_client.app, "reqAccountSummary"
        ) as mock_method:
            # Test
            self.broker_client.request_account_summary()

            # Validate
            mock_method.assert_called_once_with(
                10, "All", expected_tags_string
            )


if __name__ == "__main__":
    unittest.main()
