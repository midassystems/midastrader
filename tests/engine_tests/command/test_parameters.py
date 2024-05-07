import random
import unittest
from datetime import datetime

from midas.engine.command import Parameters

from midas.shared.utils import iso_to_unix
from midas.shared.market_data import MarketDataType
from midas.shared.symbol import Equity, Future, Currency, Venue, Symbol, Industry,ContractUnits


#TODO: Edge cases

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
        self.valid_benchmark = ["^GSPC"]
        
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
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
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
        self.assertEqual(params.benchmark, self.valid_benchmark)
        
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
        self.assertEqual(params.benchmark, None)
        
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
                    symbols=self.valid_symbols,
                    benchmark=self.valid_benchmark)
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
        self.assertEqual(params_dict["benchmark"], self.valid_benchmark)

        tickers = [symbol.ticker for symbol in self.valid_symbols]
        self.assertEqual(params_dict["tickers"], tickers)

    # Type Validation
    def test_strategy_name_type_validation(self):
        with self.assertRaisesRegex(TypeError,"strategy_name must be of type str"):
             Parameters(strategy_name=123,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
             
    def test_capital_type_validation(self):
        with self.assertRaisesRegex(TypeError,"capital must be of type int or float"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital="1000",
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)

    def test_data_type_type_validation(self):
        with self.assertRaisesRegex(TypeError,"data_type must be an instance of MarketDataType"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type="BAR",
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)

    def test_missing_values_strategy_type_validation(self):
        with self.assertRaisesRegex(TypeError, "missing_values_strategy must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=1234,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)

    def test_train_start_type_validation(self):
        with self.assertRaisesRegex(TypeError,"train_start must be of type str or None"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=datetime(2020,10, 10),
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
             
    def test_train_end_type_validation(self):
        with self.assertRaisesRegex(TypeError,"train_end must be of type str or None"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_test_start,
                            train_end=datetime(2020,10, 10),
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
             
    def test_test_start_type_validation(self):
        with self.assertRaisesRegex(TypeError,"test_start must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=datetime(2020,10, 10),
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
             
    def test_test_end_type_validation(self):
        with self.assertRaisesRegex(TypeError,"test_end must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=datetime(2020,10, 10),
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
             
    def test_benchmark_list_type_validation(self):
        with self.assertRaisesRegex(TypeError,"benchmark must be of type list or None"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark='test')
             
    def test_benchmark_list_contents_type_validation(self):
        with self.assertRaisesRegex(TypeError,"All items in 'benchmark' must be of type str"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=[9,9])
             
    def test_symbols_list_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'symbols' must be of type list"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols='tests',
                            benchmark=self.valid_benchmark)
             
    def test_symbols_list_contents_type_validation(self):
        with self.assertRaisesRegex(TypeError,"All items in 'symbols' must be instances of Symbol"):
             Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=['appl','tsla'],
                            benchmark=self.valid_benchmark)

    # Constraint Validation
    def test_missing_values_strategy_constraint(self):
        with self.assertRaisesRegex(ValueError,"'missing_values_strategy' must be either 'drop' or 'fill_forward'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy='testing',
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
    
    def test_capital_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'capital' must be greater than zero"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=-1,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_capital_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'capital' must be greater than zero"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=0,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_train_date_constraint(self):
        with self.assertRaisesRegex(ValueError,"'train_start' must be before 'train_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start='2020-01-01',
                            train_end='2019-01-01',
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_train_date_same_start_and_end_constraint(self):
        with self.assertRaisesRegex(ValueError,"'train_start' must be before 'train_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start='2020-01-01',
                            train_end='2020-01-01',
                            test_start=self.valid_test_start,
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_test_date_constraint(self):
        with self.assertRaisesRegex(ValueError,"'test_start' must be before 'test_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start='2024-02-01',
                            test_end='2024-01-01',
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_test_date_same_start_and_end_constraint(self):
        with self.assertRaisesRegex(ValueError,"'test_start' must be before 'test_end'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end=self.valid_train_end,
                            test_start='2024-01-01',
                            test_end='2024-01-01',
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_train_end_test_start_constraint(self):
        with self.assertRaisesRegex(ValueError,"'train_end' must be before 'test_start'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            train_start=self.valid_train_start,
                            train_end='2024-01-01',
                            test_start='2024-01-01',
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)
            
    def test_train_end_after_test_start_constraint(self):
        with self.assertRaisesRegex(ValueError,"'train_end' must be before 'test_start'"):
            Parameters(strategy_name=self.valid_strategy_name,
                            capital=self.valid_capital,
                            data_type=self.valid_data_type,
                            missing_values_strategy=self.valid_missing_values_strategy,
                            
                            train_start=self.valid_train_start,
                            train_end='2024-01-02',
                            test_start='2024-01-01',
                            test_end=self.valid_test_end,
                            symbols=self.valid_symbols,
                            benchmark=self.valid_benchmark)

if __name__ == "__main__":
    unittest.main()