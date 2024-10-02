import unittest
import threading
from datetime import time
from ibapi.contract import Contract
from unittest.mock import patch, Mock, MagicMock
from midas.engine.components.gateways.live.contract_manager import (
    ContractManager,
)
from midas.symbol import (
    Future,
    Equity,
    Currency,
    Venue,
    Industry,
    ContractUnits,
    SecurityType,
    FuturesMonth,
    TradingSession,
)
from midas.symbol import SymbolMap
from midas.utils.logger import SystemLogger


class TestContractManager(unittest.TestCase):
    def setUp(self) -> None:
        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # Mock broker cleint
        self.broker_client = Mock()
        self.broker_client.app = Mock()

        # Contract manager instance
        self.manager = ContractManager(self.broker_client)
        self.manager.app.validate_contract_event = threading.Event()

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

    # Basic Validation
    def change_is_valid_contract_true(self, reqId, contract):
        # Side effect for mocking reqContractdetails
        self.manager.app.is_valid_contract = True
        self.manager.app.validate_contract_event.set()

    def change_is_valid_contract_false(self, reqId, contract):
        # Side effect for mocking reqContractdetails
        self.manager.app.is_valid_contract = False
        self.manager.app.validate_contract_event.set()

    def test_validate_contract_valid_contract(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Test contract not already validated and is correclty validated
        with patch.object(
            self.manager.app,
            "reqContractDetails",
            side_effect=self.change_is_valid_contract_true,
        ) as _:
            # Test
            response = self.manager.validate_contract(contract)

            # Validate
            self.assertEqual(response, True)
            self.assertEqual(
                self.manager.validated_contracts[contract.symbol],
                contract,
            )
            self.assertTrue(self.manager.app.validate_contract_event.is_set())

    def test_validate_contract_invalid_contract(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Test contract not already validated and is not correclty validated
        with patch.object(
            self.manager.app,
            "reqContractDetails",
            side_effect=self.change_is_valid_contract_false,
        ) as _:
            # Test
            response = self.manager.validate_contract(contract)

            # Validate
            self.assertEqual(response, False)
            self.assertEqual(self.manager.validated_contracts, {})
            self.assertTrue(self.manager.app.validate_contract_event.is_set())

    def test_validate_contract_already_validate(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Add contract to validated contract log
        self.manager.validated_contracts[contract.symbol] = contract

        # Test
        response = self.manager.validate_contract(contract)

        # Validate
        self.assertEqual(response, True)  # Should return contract is valid

    def test_is_contract_validate_valid(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Add contract to validated contract log
        self.manager.validated_contracts[contract.symbol] = contract

        # Test
        response = self.manager._is_contract_validated(contract)

        # validate
        self.assertTrue(response)  # should be true, in validated contracts

    def test_is_contract_validate_invalid(self):
        contract = Contract()
        contract.symbol = "AAPL"

        # Test
        response = self.manager._is_contract_validated(contract)

        # Validate
        self.assertFalse(response)  # Should be false, invaldiated contracts

    # Type Check
    def test_validate_contract_invalid_contract_type(self):
        contract = "AAPL"
        with self.assertRaisesRegex(
            ValueError, "'contract' must be of type Contract instance."
        ):
            self.manager.validate_contract(contract)


if __name__ == "__main__":

    unittest.main()
