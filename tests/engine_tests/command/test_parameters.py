import json
import random
import unittest
from datetime import datetime
from unittest.mock import patch, mock_open
from midas.shared.utils import iso_to_unix
from midas.engine.command import Parameters
from midas.shared.market_data import MarketDataType
from midas.shared.symbol import Equity, Future, Currency, Venue, Symbol, Industry, ContractUnits

class TestParameters(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_strategy_name = "Testing"
        self.valid_capital = 1000000
        self.valid_data_type = random.choice([MarketDataType.BAR, MarketDataType.QUOTE])
        self.valid_missing_values_strategy = random.choice(['drop', 'fill_forward'])
        self.valid_strategy_allocation = 1.0
        self.valid_train_start = "2020-05-18"
        self.valid_train_end = "2023-12-31"
        self.valid_test_start = "2024-01-01"
        self.valid_test_end = "2024-01-19"
        self.valid_symbols = [
            Future(ticker = "HE",
                data_ticker = "HE.n.0",
                currency = Currency.USD,  
                exchange = Venue.CME,  
                fees = 0.85,  
                initialMargin =4564.17,
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
                lastTradeDateOrContractMonth="202404"),
            Future(ticker = "ZC",
                data_ticker = "ZC.n.0",
                currency = Currency.USD,  
                exchange = Venue.CBOT,  
                fees = 0.85,  
                initialMargin =2056.75,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202406")
        ]
        
    # Basic Validation
    def test_construction(self):
        # test
        params = Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
        # validate
        self.assertEqual(params.strategy_name, self.valid_strategy_name)
        self.assertEqual(params.capital, self.valid_capital)
        self.assertEqual(params.data_type, self.valid_data_type)
        self.assertEqual(params.missing_values_strategy, self.valid_missing_values_strategy)
        self.assertEqual(params.train_start, self.valid_train_start)
        self.assertEqual(params.train_end, self.valid_train_end)
        self.assertEqual(params.test_start, self.valid_test_start)
        self.assertEqual(params.test_end, self.valid_test_end)
        self.assertEqual(params.symbols, self.valid_symbols)
        
        tickers = [symbol.ticker for symbol in self.valid_symbols]
        self.assertEqual(params.tickers,tickers)

    def test_construction_defaults(self):
        # test
        params = Parameters(strategy_name=self.valid_strategy_name,
                    capital=self.valid_capital,
                    data_type=self.valid_data_type,
                    test_start=self.valid_test_start,
                    test_end=self.valid_test_end,
                    symbols=self.valid_symbols)
        # validate              
        self.assertEqual(params.strategy_name, self.valid_strategy_name)
        self.assertEqual(params.capital, self.valid_capital)
        self.assertEqual(params.data_type, self.valid_data_type)
        self.assertEqual(params.missing_values_strategy, 'fill_forward')
        self.assertEqual(params.train_start, None)
        self.assertEqual(params.train_end, None)
        self.assertEqual(params.test_start, self.valid_test_start)
        self.assertEqual(params.test_end, self.valid_test_end)
        self.assertEqual(params.symbols, self.valid_symbols)
        
        tickers = [symbol.ticker for symbol in self.valid_symbols]
        self.assertEqual(params.tickers,tickers)

    def test_to_dict(self):
        params = Parameters(strategy_name=self.valid_strategy_name,
                    capital=self.valid_capital,
                    data_type=self.valid_data_type,
                    missing_values_strategy=self.valid_missing_values_strategy,
                    train_start=self.valid_train_start,
                    train_end=self.valid_train_end,
                    test_start=self.valid_test_start,
                    test_end=self.valid_test_end,
                    symbols=self.valid_symbols)
        # test
        params_dict = params.to_dict()

        # validate
        self.assertEqual(params_dict["strategy_name"], self.valid_strategy_name)
        self.assertEqual(params_dict["capital"], self.valid_capital)
        self.assertEqual(params_dict["data_type"], self.valid_data_type.value)
        self.assertEqual(params_dict["train_start"], iso_to_unix(self.valid_train_start))
        self.assertEqual(params_dict["train_end"], iso_to_unix(self.valid_train_end))
        self.assertEqual(params_dict["test_start"], iso_to_unix(self.valid_test_start))
        self.assertEqual(params_dict["test_end"], iso_to_unix(self.valid_test_end))

        tickers = [symbol.ticker for symbol in self.valid_symbols]
        self.assertEqual(params_dict["tickers"], tickers)

    def test_from_file(self):
        # Mock JSON data
        mock_config = {
    "strategy_name": "TestStrategy",
    "missing_values_strategy": "fill_forward",
    "train_start": "2020-01-01",
    "train_end": "2023-01-01",
    "test_start": "2023-02-01",
    "test_end": "2023-12-31",
    "capital": 1000000,
    "data_type": "BAR",
    "symbols": [
        {
            "type": "Future",
            "ticker" : "HE",
            "data_ticker" : "HE.n.0",
            "security_type": "FUTURE",
            "currency": "USD",
            "exchange": "CME",
            "fees": 0.85,
            "initialMargin": 5627.17,
            "quantity_multiplier": 40000,
            "price_multiplier": 0.01,
            "data_ticker": "HE.n.0",
            "product_code": "HE",
            "product_name": "Lean Hogs",
            "industry": "AGRICULTURE",
            "contract_size": 40000,
            "contract_units": "POUNDS",
            "tick_size": 0.00025,
            "min_price_fluctuation": 10.0,
            "continuous": True,
            "lastTradeDateOrContractMonth": "202404",
            "slippage_factor": 0
        },
        {
            "type": "Future",
            "ticker" : "ZC",
            "data_ticker" : "ZC.n.0",
            "security_type": "FUTURE",
            "currency": "USD",
            "exchange": "CBOT",
            "fees": 0.85,
            "initialMargin": 2075.36,
            "quantity_multiplier": 5000,
            "price_multiplier": 0.01,
            "data_ticker": "ZC.n.0",
            "product_code": "ZC",
            "product_name": "Corn",
            "industry": "AGRICULTURE",
            "contract_size": 5000,
            "contract_units": "BUSHELS",
            "tick_size": 0.0025,
            "min_price_fluctuation": 12.50,
            "continuous": True,
            "lastTradeDateOrContractMonth": "202404",
            "slippage_factor": 0
        }
    ]
}

        # Use patch to mock open() and return the mock_config
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config))):
            params = Parameters.from_file("test_config.json")

        # Validate
        self.assertEqual(params.strategy_name, "TestStrategy")
        self.assertEqual(params.capital, 1000000)
        self.assertEqual(params.data_type, MarketDataType.BAR)
        self.assertEqual(params.missing_values_strategy, "fill_forward")
        self.assertEqual(params.train_start, "2020-01-01")
        self.assertEqual(params.train_end, "2023-01-01")
        self.assertEqual(params.test_start, "2023-02-01")
        self.assertEqual(params.test_end, "2023-12-31")

        # Validate symbols
        self.assertEqual(len(params.symbols), 2)
        self.assertIsInstance(params.symbols[0], Future)
        self.assertIsInstance(params.symbols[1], Future)
        self.assertEqual(params.symbols[0].ticker, "HE")
        print(params.symbols)
        self.assertEqual(params.symbols[1].ticker, "ZC")

    # Type Validation
    def test_type_errors(self):
        with self.assertRaisesRegex(TypeError,"strategy_name must be of type str"):
             Parameters(strategy_name=123,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
             
        with self.assertRaisesRegex(TypeError,"capital must be of type int or float"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital="1000",
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)

        with self.assertRaisesRegex(TypeError,"data_type must be an instance of MarketDataType"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type="BAR",
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)

        with self.assertRaisesRegex(TypeError, "missing_values_strategy must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=1234,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)

        with self.assertRaisesRegex(TypeError,"train_start must be of type str or None"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=datetime(2020,10, 10),
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
             
        with self.assertRaisesRegex(TypeError,"train_end must be of type str or None"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_test_start,
                            train_end=datetime(2020,10, 10),
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
             
        with self.assertRaisesRegex(TypeError,"test_start must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=datetime(2020,10, 10),
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
             
        with self.assertRaisesRegex(TypeError,"test_end must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=datetime(2020,10, 10),
                            symbols=self.valid_symbols)
             
        with self.assertRaisesRegex(TypeError,"'symbols' must be of type list"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols='tests')
             
        with self.assertRaisesRegex(TypeError,"All items in 'symbols' must be instances of Symbol"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=['appl','tsla'])

    # Constraint Validation
    def test_value_constraints(self):
        with self.assertRaisesRegex(ValueError,"'missing_values_strategy' must be either 'drop' or 'fill_forward'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy='testing',
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
    
        with self.assertRaisesRegex(ValueError,"'capital' must be greater than zero"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=-1,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'capital' must be greater than zero"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=0,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'train_start' must be before 'train_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start='2020-01-01',
                            train_end='2019-01-01',
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'train_start' must be before 'train_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start='2020-01-01',
                            train_end='2020-01-01',
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'test_start' must be before 'test_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start='2024-02-01',
                            test_end='2024-01-01',
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'test_start' must be before 'test_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start='2024-01-01',
                            test_end='2024-01-01',
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'train_end' must be before 'test_start'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end='2024-01-01',
                            test_start='2024-01-01',
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)
            
        with self.assertRaisesRegex(ValueError,"'train_end' must be before 'test_start'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end='2024-01-02',
                            test_start='2024-01-01',
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols)

if __name__ == "__main__":
    unittest.main()