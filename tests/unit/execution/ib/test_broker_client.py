import unittest
import threading
from time import sleep
from datetime import time
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from midastrader.structs.events import OrderEvent
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.orders import Action, MarketOrder
from midastrader.structs.symbol import SymbolMap
from midastrader.execution.adaptors.ib.client import IBAdaptor
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


class TestIBDataAdaptor(unittest.TestCase):
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

        # Mock Config
        self.kwargs = {
            "host": 1,
            "port": 2,
            "client_id": 0,
            "account_id": "1234",
        }

        self.bus = MessageBus()

        # DataClient instance
        self.adapter = IBAdaptor(self.symbols_map, self.bus, **self.kwargs)

        # Mock data wrapper
        self.adapter.app = Mock()
        self.adapter.app.reqId_to_instrument = {}
        self.adapter.app.validate_contract_event = threading.Event()

    # Basic Validation
    def test_get_valid_id(self):
        # Set next validId
        id = 10
        self.adapter.app.next_valid_order_id = id

        # Test
        current_id = self.adapter._get_valid_id()

        # Validate
        self.assertEqual(current_id, id)
        self.assertEqual(self.adapter.app.next_valid_order_id, id + 1)

    def test_is_connected(self):
        # Test
        self.adapter.app.isConnected = Mock(return_value=True)

        # Validate
        self.assertTrue(self.adapter.is_connected())
        self.adapter.app.isConnected.assert_called_once()

    def test_connect(self):
        self.adapter._get_valid_id = Mock(return_value=1)
        self.adapter.validate_contract = Mock(return_value=True)

        # Ensure connect method starts a thread and waits for connection events
        with patch(
            "threading.Thread.start", return_value=None
        ) as mock_thread_start:
            self.adapter.app.connected_event.wait = Mock()
            self.adapter.app.valid_id_event.wait = Mock()

            # Test
            self.adapter.connect()

            # Validate
            mock_thread_start.assert_called_once()
            self.adapter.app.connected_event.wait.assert_called_once()
            self.adapter.app.valid_id_event.wait.assert_called_once()

    def test_disconnect(self):
        self.adapter.app.disconnect = Mock()

        # Test
        self.adapter.disconnect()

        # Validate
        self.adapter.app.disconnect.assert_called_once()

    def test_process(self):
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
        self.adapter.connect = Mock()
        self.adapter.handle_order = Mock()
        threading.Thread(target=self.adapter.process, daemon=True).start()
        self.bus.publish(EventType.ORDER, event)
        sleep(1)

        # Validate
        args = self.adapter.handle_order.call_args[0]
        self.assertEqual(args[0], event)

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
        self.adapter._get_valid_id = Mock(return_value=1)
        self.adapter.app.placeOrder = Mock()
        self.adapter.handle_order(event)

        # Validate
        self.assertEqual(self.adapter.app.placeOrder.call_count, 1)

    def test_request_account_summary(self):
        self.adapter._get_valid_id = Mock(return_value=10)
        expected_tags_string = "Timestamp,FullAvailableFunds,FullInitMarginReq,NetLiquidation,UnrealizedPnL,FullMaintMarginReq,ExcessLiquidity,Currency,BuyingPower,FuturesPNL,TotalCashBalance"

        with patch.object(
            self.adapter.app, "reqAccountSummary"
        ) as mock_method:
            # Test
            self.adapter.request_account_summary()

            # Validate
            mock_method.assert_called_once_with(
                10, "All", expected_tags_string
            )

    # Basic Validation
    def change_is_valid_contract_true(self, reqId, contract):
        # Side effect for mocking reqContractdetails
        self.adapter.app.is_valid_contract = True
        self.adapter.app.validate_contract_event.set()

    def change_is_valid_contract_false(self, reqId, contract):
        # Side effect for mocking reqContractdetails
        self.adapter.app.is_valid_contract = False
        self.adapter.app.validate_contract_event.set()

    def test_validate_contract_valid_contract(self):
        self.adapter._get_valid_id = Mock(return_value=1)
        contract = Contract()
        contract.symbol = "AAPL"

        # Test contract not already validated and is correclty validated
        with patch.object(
            self.adapter.app,
            "reqContractDetails",
            side_effect=self.change_is_valid_contract_true,
        ) as _:
            # Test
            response = self.adapter.validate_contract(contract)

            # Validate
            self.assertEqual(response, True)
            self.assertEqual(
                self.adapter.validated_contracts[contract.symbol],
                contract,
            )
            self.assertTrue(self.adapter.app.validate_contract_event.is_set())

    def test_validate_contract_invalid_contract(self):
        self.adapter._get_valid_id = Mock(return_value=1)
        contract = Contract()
        contract.symbol = "AAPL"

        # Test contract not already validated and is not correclty validated
        with patch.object(
            self.adapter.app,
            "reqContractDetails",
            side_effect=self.change_is_valid_contract_false,
        ) as _:
            # Test
            response = self.adapter.validate_contract(contract)

            # Validate
            self.assertEqual(response, False)
            self.assertEqual(self.adapter.validated_contracts, {})
            self.assertTrue(self.adapter.app.validate_contract_event.is_set())

    def test_validate_contract_already_validate(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Add contract to validated contract log
        self.adapter.validated_contracts[contract.symbol] = contract

        # Test
        response = self.adapter.validate_contract(contract)

        # Validate
        self.assertEqual(response, True)  # Should return contract is valid

    def test_is_contract_validate_valid(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Add contract to validated contract log
        self.adapter.validated_contracts[contract.symbol] = contract

        # Test
        response = self.adapter._is_contract_validated(contract)

        # validate
        self.assertTrue(response)  # should be true, in validated contracts

    def test_is_contract_validate_invalid(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Test
        response = self.adapter._is_contract_validated(contract)

        # Validate
        self.assertFalse(response)  # Should be false, invaldiated contracts

    # Type Check
    def test_validate_contract_invalid_contract_type(self):
        contract = "AAPL"
        with self.assertRaisesRegex(
            ValueError, "'contract' must be of type Contract instance."
        ):
            self.adapter.validate_contract(contract)  # pyright: ignore


if __name__ == "__main__":
    unittest.main()
