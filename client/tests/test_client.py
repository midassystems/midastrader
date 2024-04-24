import copy
import logging
import unittest
from decimal import Decimal
from decouple import config

from client import DatabaseClient

from shared.symbol import Symbol,Equity, SecurityType, Currency, Future, Option, Index, AssetClass, ContractUnits, Venue, Industry, Right
from shared.market_data import *
from shared.backtest import Backtest
from shared.live_session import LiveTradingSession


DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

class TestSymbolDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

    @classmethod
    def tearDownClass(cls):

        logging.basicConfig(level=logging.DEBUG)

        resources = [
            ("asset classes", cls.client.get_asset_classes, cls.client.delete_asset_class),
            ("security types", cls.client.get_security_types, cls.client.delete_security_type),
            ("venues", cls.client.get_venues, cls.client.delete_venue),
            ("currencies", cls.client.get_currencies, cls.client.delete_currency),
            ("industries", cls.client.get_industries, cls.client.delete_industry),
            ("contract units", cls.client.get_contract_units, cls.client.delete_contract_units)
        ]

        for name, getter, deleter in resources:
            try:
                items = getter()
                for item in items:
                    try:
                        deleter(item["id"])
                        logging.debug(f"Successfully deleted {name[:-1]} with ID: {item['id']}")
                    except Exception as e:
                        logging.error(f"Failed to delete {name[:-1]} with ID: {item['id']}: {e}")
            except Exception as e:
                logging.error(f"Failed to retrieve {name}: {e}")

    def test_create_asset_class(self):
        asset_class = AssetClass.FIXED_INCOME
        
        # Test
        response = self.client.create_asset_class(asset_class)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],asset_class.value)

    def test_create_asset_class_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_asset_class("asset_class")

    def test_get_asset_class(self):
        asset_class = AssetClass.CRYPTOCURRENCY
        self.client.create_asset_class(asset_class)
        
        # Test
        response = self.client.get_asset_classes()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_asset_class(self):
        asset_class = AssetClass.COMMODITY
        old_response = self.client.create_asset_class(asset_class)
        
        # Test
        response = self.client.update_asset_class(old_response["id"], AssetClass.FOREX)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], "FOREX")
        self.assertTrue(response["id"], old_response["id"])

    def test_create_security_type(self):
        security_type = SecurityType.CRYPTO
        
        # Test
        response = self.client.create_security_type(security_type)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],security_type.value)

    def test_create_security_type_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_security_type("security_type")

    def test_get_security_type(self):
        security_type = SecurityType.BOND
        self.client.create_security_type(security_type)
        
        # Test
        response = self.client.get_security_types()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_security_type(self):
        security_type = SecurityType.OPTION
        old_response = self.client.create_security_type(security_type)
        
        # Test
        new_security_type = SecurityType.INDEX
        response = self.client.update_security_type(old_response["id"], new_security_type)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], new_security_type.value)
        self.assertTrue(response["id"], old_response["id"])

    def test_create_venue(self):
        venue = Venue.CBOT
        
        # Test
        response = self.client.create_venue(venue)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],venue.value)

    def test_create_venue_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_venue("venue")

    def test_get_venue(self):
        venue = Venue.CBOE
        self.client.create_venue(venue)
        
        # Test
        response = self.client.get_venues()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_venue(self):
        venue = Venue.GLOBEX
        old_response = self.client.create_venue(venue)
        
        # Test
        new_venue = Venue.NYSE
        response = self.client.update_venue(old_response["id"], new_venue)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], new_venue.value)
        self.assertTrue(response["id"], old_response["id"])

    def test_create_currency(self):
        currency = Currency.CAD
        
        # Test
        response = self.client.create_currency(currency)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],currency.value)

    def test_create_currency_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_currency("currency")

    def test_get_currency(self):
        currency = Currency.AUD
        self.client.create_currency(currency)
        
        # Test
        response = self.client.get_currencies()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_currency(self):
        currency = Currency.JPY
        old_response = self.client.create_currency(currency)
        
        # Test
        new_currency = Currency.GBP
        response = self.client.update_currency(old_response["id"], new_currency)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], new_currency.value)
        self.assertTrue(response["id"], old_response["id"])

    def test_create_industry(self):
        industry = Industry.CONSUMER
        
        # Test
        response = self.client.create_industry(industry)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],industry.value)

    def test_create_industry_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_industry("industry")

    def test_get_industry(self):
        industry = Industry.MATERIALS
        self.client.create_industry(industry)
        
        # Test
        response = self.client.get_industries()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_industry(self):
        industry = Industry.COMMUNICATION
        old_response = self.client.create_industry(industry)
        
        # Test
        new_industry = Industry.METALS
        response = self.client.update_industry(old_response["id"], new_industry)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], new_industry.value)
        self.assertTrue(response["id"], old_response["id"])

    def test_create_contract_units(self):
        contract_units = ContractUnits.BARRELS
        
        # Test
        response = self.client.create_contract_units(contract_units)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertEqual(response["value"],contract_units.value)

    def test_create_contract_units_invalid(self):
        with self.assertRaises(TypeError):
            self.client.create_contract_units("contract_units")

    def test_get_contract_units(self):
        contract_units = ContractUnits.BUSHELS
        self.client.create_contract_units(contract_units)
        
        # Test
        response = self.client.get_contract_units()

        # Validate
        self.assertTrue(len(response) > 0)

    def test_update_contract_units(self):
        contract_units = ContractUnits.METRIC_TON
        old_response = self.client.create_contract_units(contract_units)
        
        # Test
        new_contract_units = ContractUnits.TROY_OUNCE
        response = self.client.update_contract_units(old_response["id"], new_contract_units)

        # Validate
        self.assertTrue(len(response) > 0)
        self.assertTrue(response["value"], new_contract_units.value)
        self.assertTrue(response["id"], old_response["id"])

class TestSymbolMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

        cls.client.create_security_type(SecurityType.STOCK)
        cls.client.create_currency(Currency.USD)
        cls.client.create_venue(Venue.NASDAQ)
        cls.client.create_industry(Industry.TECHNOLOGY)
        
        cls.equity = Equity(ticker="TSLA",
                        security_type=SecurityType.STOCK,
                        currency = Currency.USD,  
                        exchange = Venue.NASDAQ,  
                        fees = 0.1,
                        initialMargin = 0,
                        quantity_multiplier=1,
                        price_multiplier=1,
                        data_ticker = "AAPL2",
                        company_name = "Apple Inc.",
                        industry=Industry.TECHNOLOGY,
                        market_cap=10000000000.99,
                        shares_outstanding=1937476363)


        cls.client.create_security_type(SecurityType.FUTURE)
        cls.client.create_venue(Venue.CME)
        cls.client.create_industry(Industry.AGRICULTURE)
        cls.client.create_contract_units(ContractUnits.POUNDS)

        cls.future = Future(ticker = "HEJ4",
                                security_type = SecurityType.FUTURE,
                                data_ticker = "HE.n.0" ,
                                currency = Currency.USD , 
                                exchange = Venue.CME  ,
                                fees = 0.1,
                                initialMargin = 4000.598,
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
                                lastTradeDateOrContractMonth="202406")

        cls.client.create_security_type(SecurityType.OPTION)

        cls.option = Option(ticker = "AAPLP",
                                security_type = SecurityType.OPTION,
                                data_ticker = "AAPL",
                                currency = Currency.USD,  
                                exchange = Venue.NASDAQ,  
                                fees = 0.1,
                                initialMargin = 0,
                                quantity_multiplier=100,
                                price_multiplier=1,
                                strike_price=109.99,
                                expiration_date="2024-01-01",
                                option_type=Right.CALL,
                                contract_size=100,
                                underlying_name="AAPL",
                                lastTradeDateOrContractMonth="20240201")
        
        cls.client.create_security_type(SecurityType.INDEX)
        cls.client.create_venue(Venue.INDEX)
        cls.client.create_asset_class(AssetClass.EQUITY)
        
        cls.index = Index(ticker="GSPC",
                            security_type=SecurityType.INDEX,
                            name="S&P 500",
                            currency=Currency.USD,
                            asset_class=AssetClass.EQUITY)

    @classmethod
    def tearDownClass(cls) -> None:
        # delete symbol details
        resources = [
            ("asset classes", cls.client.get_asset_classes, cls.client.delete_asset_class),
            ("security types", cls.client.get_security_types, cls.client.delete_security_type),
            ("venues", cls.client.get_venues, cls.client.delete_venue),
            ("currencies", cls.client.get_currencies, cls.client.delete_currency),
            ("industries", cls.client.get_industries, cls.client.delete_industry),
            ("contract units", cls.client.get_contract_units, cls.client.delete_contract_units)
        ]

        for name, getter, deleter in resources:
            try:
                items = getter()
                for item in items:
                    try:
                        deleter(item["id"])
                        logging.debug(f"Successfully deleted {name[:-1]} with ID: {item['id']}")
                    except Exception as e:
                        logging.error(f"Failed to delete {name[:-1]} with ID: {item['id']}: {e}")
            except Exception as e:
                logging.error(f"Failed to retrieve {name}: {e}")

        # delete symbols
        def delete_symbol(symbol: Symbol):
            try:
                response = cls.client.get_symbol_by_ticker(symbol.ticker)
                if len(response) == 0:
                    logging.debug(f"No symbol found for ticker {symbol.ticker}, nothing to delete.")
                elif len(response) == 1:
                    cls.client.delete_symbol(response[0]['id'])
                    # Verify deletion
                    verification = cls.client.get_symbol_by_ticker(symbol.ticker)
                    if len(verification) == 0:
                        logging.debug(f"Successfully deleted symbol with ticker {symbol.ticker}.")
                    else:
                        logging.error(f"Failed to delete symbol with ticker {symbol.ticker}, it still exists.")
                else:
                    logging.error(f"Multiple entries found for ticker {symbol.ticker}, not deleting.")
            except Exception as e:
                logging.error(f"Error deleting symbol for ticker {symbol.ticker}: {e}")

        delete_symbol(cls.equity)
        delete_symbol(cls.future)
        delete_symbol(cls.option)
        delete_symbol(cls.index)

    def test_create_symbol_equity(self):
        # test 
        response = self.client.create_symbol(self.equity)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.equity.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_future(self):
        # test 
        response = self.client.create_symbol(self.future)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.future.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_option(self):
        # test 
        response = self.client.create_symbol(self.option)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.option.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_index(self):
        # test 
        response = self.client.create_symbol(self.index)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.index.ticker)

        self.client.delete_symbol(response["id"])

    def test_update_symbol(self):
        equity = self.equity
        equity.ticker = "Test8"
        old_response=self.client.create_symbol(equity)

        # test
        equity.ticker = "Test9"
        response=self.client.update_symbol(symbol_id=old_response["id"], symbol=equity)

        # validate
        self.assertEqual(old_response["id"], response["id"])
        self.assertEqual(response["ticker"], equity.ticker)

        # clean up
        self.client.delete_symbol(response["id"])

    def test_delete_symbol(self):  
        symbol = self.client.create_symbol(self.equity) 

        # test 
        self.client.delete_symbol(symbol["id"])

        # validate
        response=self.client.get_symbols()
        for i in response:
            self.assertTrue(i["ticker"] != "TSLA")

    def test_get_symbol_by_ticker(self):
        ticker="HEJ4"
        symbol=self.client.create_symbol(self.future)
        
        # test
        response=self.client.get_symbol_by_ticker(ticker)[0]

        # Validate
        self.assertEqual(response["ticker"], ticker)
        self.assertEqual(response["security_type"], "FUT")
        
        # clean up
        self.client.delete_symbol(symbol["id"])

    def test_get_symbols_list(self):
        response_eq=self.client.create_symbol(self.equity)
        response_fu = self.client.create_symbol(self.future)

        # test
        response=self.client.get_symbols()

        # validate
        tickers=[]
        for i in response:
            tickers.append(i['ticker'])

        self.assertGreaterEqual(len(response), 1)
        self.assertIn(self.future.ticker,tickers)
        self.assertIn(self.equity.ticker,tickers)

        # clean up
        self.client.delete_symbol(response_fu["id"])
        self.client.delete_symbol(response_eq["id"])
            
    def test_get_equity_list(self):
        symbol=self.client.create_symbol(self.equity)

        # test
        response=self.client.get_equity()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean-up
        self.client.delete_symbol(symbol["id"])

    def test_get_future_list(self):
        symbol=self.client.create_symbol(self.future)

        # test
        response=self.client.get_future()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean up
        self.client.delete_symbol(symbol["id"])

    def test_get_indexes_list(self):
        symbol = self.client.create_symbol(self.index)

        # test
        response=self.client.get_indexes()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean-up
        self.client.delete_symbol(symbol["id"])

    # def test_get_options_list(self):
    #     # test
    #     response=self.client.get_options()
        
    #     # validate
    #     self.assertGreaterEqual(len(response), 1)

class TestBarDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        cls.ticker="AAPL4"

        cls.client.create_security_type(SecurityType.STOCK)
        cls.client.create_currency(Currency.USD)
        cls.client.create_venue(Venue.NASDAQ)
        cls.client.create_industry(Industry.TECHNOLOGY)

        cls.equity = Equity(ticker="AAPL4",
                                security_type=SecurityType.STOCK,
                                company_name="Apple Inc.",
                                exchange=Venue.NASDAQ,
                                currency=Currency.USD,
                                industry=Industry.TECHNOLOGY,
                                market_cap=10000000000.99,
                                shares_outstanding=1937476363,
                                fees=0.1,
                                initialMargin=0,
                                quantity_multiplier=1,
                                price_multiplier=1)
        cls.symbol=cls.client.create_symbol(cls.equity)

    @classmethod
    def tearDownClass(cls) -> None:
        # delete symbol details
        resources = [
            ("asset classes", cls.client.get_asset_classes, cls.client.delete_asset_class),
            ("security types", cls.client.get_security_types, cls.client.delete_security_type),
            ("venues", cls.client.get_venues, cls.client.delete_venue),
            ("currencies", cls.client.get_currencies, cls.client.delete_currency),
            ("industries", cls.client.get_industries, cls.client.delete_industry),
            ("contract units", cls.client.get_contract_units, cls.client.delete_contract_units)
        ]

        for name, getter, deleter in resources:
            try:
                items = getter()
                for item in items:
                    try:
                        deleter(item["id"])
                        logging.debug(f"Successfully deleted {name[:-1]} with ID: {item['id']}")
                    except Exception as e:
                        logging.error(f"Failed to delete {name[:-1]} with ID: {item['id']}: {e}")
            except Exception as e:
                logging.error(f"Failed to retrieve {name}: {e}")

        # delete symbols
        def delete_symbol(symbol: Symbol):
            try:
                response = cls.client.get_symbol_by_ticker(symbol.ticker)
                if len(response) == 0:
                    logging.debug(f"No symbol found for ticker {symbol.ticker}, nothing to delete.")
                elif len(response) == 1:
                    cls.client.delete_symbol(response[0]['id'])
                    # Verify deletion
                    verification = cls.client.get_symbol_by_ticker(symbol.ticker)
                    if len(verification) == 0:
                        logging.debug(f"Successfully deleted symbol with ticker {symbol.ticker}.")
                    else:
                        logging.error(f"Failed to delete symbol with ticker {symbol.ticker}, it still exists.")
                else:
                    logging.error(f"Multiple entries found for ticker {symbol.ticker}, not deleting.")
            except Exception as e:
                logging.error(f"Error deleting symbol for ticker {symbol.ticker}: {e}")

        delete_symbol(cls.equity)
    
    def setUp(self) -> None:
        self.bar=BarData(ticker="AAPL4",
                            timestamp=np.uint64(1711100000000000000),
                            open=Decimal('99.9999'),
                            high=Decimal('100.9999'),
                            low=Decimal('100.9999'),
                            close=Decimal('100.9999'),
                            volume=np.uint64(100),
                            )
        
        self.bar2 = copy.deepcopy(self.bar)
        self.bar2.timestamp = np.uint64(1711200000000000000)

        self.bar3 = copy.deepcopy(self.bar)
        self.bar3.timestamp = np.uint64(1711300000000000000)

        self.bars = [self.bar2,self.bar3]

    def test_create_bar_data(self):
        # test
        response=self.client.create_bar_data(self.bar)

        # valdiate
        self.assertIn( "id", response)
        self.assertEqual(response['symbol'], self.bar.ticker)
        self.assertEqual(response['timestamp'], self.bar.timestamp)
        self.assertEqual(Decimal(response['open']), self.bar.open)
        self.assertEqual(Decimal(response['high']), self.bar.high)
        self.assertEqual(Decimal(response['low']), self.bar.low)
        self.assertEqual(Decimal(response['close']), self.bar.close)
        self.assertEqual(response['volume'], self.bar.volume)

    def test_get_bar_data_ticker_and_dates(self):

        bar=BarData(ticker="AAPL4",
                    timestamp=np.uint64(1712400000000000000),
                    open=Decimal('99.9999'),
                    high=Decimal('100.9999'),
                    low=Decimal('100.9999'),
                    close=Decimal('100.9999'),
                    volume=np.uint64(100),
                    )
        self.client.create_bar_data(bar)
        tickers=[self.ticker]
        start_date="2020-01-01"
        end_date="2025-02-02"
        
        # test
        response=self.client.get_bar_data(tickers, start_date, end_date)

        # valdiate
        self.assertGreaterEqual(len(response), 1)


    def test_create_bulk_bar_data(self):
        # test
        response=self.client.create_bulk_price_data(self.bars)

        # validate
        self.assertEqual(len(response['batch_responses'][0]['created']), 2)
        self.assertEqual(len(response['batch_responses'][0]['errors']), 0)

    def test_create_bulk_bar_data_with_overlap(self):
        bar4 = copy.deepcopy(self.bar)
        bar4.timestamp = 1707221190000000000

        self.bars.append(bar4)
        
        # test
        response= self.client.create_bulk_price_data(self.bars)

        # validate
        self.assertEqual(len(response['batch_responses'][0]['created']), 1)
        self.assertEqual(len(response['batch_responses'][0]['errors']), 2)

    def test_update_data(self):

        bar=BarData(ticker="AAPL4",
                    timestamp=np.uint64(1712200000000000000),
                    open=Decimal('99.9999'),
                    high=Decimal('100.9999'),
                    low=Decimal('100.9999'),
                    close=Decimal('100.9999'),
                    volume=np.uint64(100),
                    )
        self.client.create_bar_data(bar)

        tickers=[self.ticker]
        start_date="2024-03-01"
        end_date="2024-05-01"
        old_bar=self.client.get_bar_data(tickers, start_date, end_date)[0]

        new_bar = copy.deepcopy(self.bar)
        new_bar.open = Decimal("0.0009")

        # test
        response=self.client.update_bar_data(old_bar['id'], new_bar)

        # validate
        self.assertEqual(old_bar['id'], response['id'])
        self.assertEqual(Decimal(response['open']), new_bar.open)

class TestBacktestMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": 1526601600000000000, 
                                "train_end": 1674086400000000000, 
                                "test_start": 1674086400000000000, 
                                "test_end": 1705622400000000000, 
                                "tickers": ["AAPL"], 
                                "benchmark": ["^GSPC"]
                            }
        self.mock_static_stats = [{
                                "net_profit": 330.0, 
                                "total_fees": 40.0, 
                                "total_return": 0.33, 
                                "ending_equity": 1330.0, 
                                "max_drawdown": 0.0, 
                                "total_trades": 2, 
                                "num_winning_trades": 2, 
                                "num_lossing_trades": 0, 
                                "avg_win_percent": 0.45, 
                                "avg_loss_percent": 0, 
                                "percent_profitable": 1.0, 
                                "profit_and_loss": 0.0, 
                                "profit_factor": 0.0, 
                                "avg_trade_profit": 165.0, 
                                "sortino_ratio": 0.0
                            }]
        self.mock_regression_stats=[{
                                "r_squared": "1.0", 
                                "p_value_alpha": "0.5", 
                                "p_value_beta": "0.09", 
                                "risk_free_rate": "0.01", 
                                "alpha": "16.4791", 
                                "beta": "-66.6633", 
                                "sharpe_ratio": "10.72015", 
                                "annualized_return": "39.0001", 
                                "market_contribution": "-0.498",
                                "idiosyncratic_contribution": "0.66319",
                                "total_contribution": "0.164998", 
                                "annualized_volatility": "3.7003", 
                                "market_volatility": "-0.25608",
                                "idiosyncratic_volatility": "7.85876", 
                                "total_volatility": "0.23608", 
                                "portfolio_dollar_beta": "-8862.27533", 
                                "market_hedge_nmv": "88662.2533"
                            }]
        self.mock_timeseries_stats =  [
                                {
                                    "timestamp": 1702141200000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": 1702227600000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.087", 
                                    "daily_benchmark_return": "0.009"
                                }
                            ]
        self.mock_trades =  [{
                                "trade_id": 1, 
                                "leg_id": 1, 
                                "timestamp": 1672704000000000000, 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "price": 130.74, 
                                "cost": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.mock_signals =  [{
                                "timestamp": 1672704000000000000, 
                                "trade_instructions": [{
                                    "ticker": "AAPL", 
                                    "action": "BUY", 
                                    "trade_id": 1, 
                                    "leg_id": 1, 
                                    "weight": 0.05
                                }, 
                                {
                                    "ticker": "MSFT", 
                                    "action": "SELL", 
                                    "trade_id": 1, 
                                    "leg_id": 2, 
                                    "weight": 0.05
                                }]
                            }]
        
        self.backtest = Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats=self.mock_regression_stats,
                                 timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)

    def test_create_backtest(self):
        # test
        response =self.client.create_backtest(self.backtest)

        # validate
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)

    def test_get_backtest(self):
        # test
        response=self.client.get_backtests()

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("id", response[0])
        self.assertIn("strategy_name", response[0])
        self.assertIn("tickers", response[0])
        self.assertIn("benchmark", response[0])
        self.assertIn("data_type", response[0])
        self.assertIn("train_start", response[0])
        self.assertIn("train_end", response[0])
        self.assertIn("test_start", response[0])
        self.assertIn("test_end", response[0])
        self.assertIn("capital", response[0])
    
    def test_get_backtest_by_id(self):
        response =self.client.create_backtest(self.backtest)

        # test
        response=self.client.get_specific_backtest(response['id'])

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)
        self.assertIn("price_data", response)

class TestTradingSessioMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": 1526601600000000000, 
                                "train_end": 1674086400000000000, 
                                "test_start": 1674086400000000000, 
                                "test_end": 1705622400000000000,  
                                "tickers": ["HE", "ZC"], 
                                "benchmark": ["^GSPC"]
                            }
        
        ac = [{
                'start_BuyingPower': '2533616.6400', 
                'currency': 'USD', 
                'start_ExcessLiquidity': '761628.7100', 
                'start_FullAvailableFunds': '760084.9900', 
                'start_FullInitMarginReq': '8009.9500', 
                'start_FullMaintMarginReq': '6466.2300', 
                'start_FuturesPNL': '-510.3400', 
                'start_NetLiquidation': '768094.9400', 
                'start_TotalCashBalance': '-11655.0816', 
                'start_UnrealizedPnL': '1.2100', 
                'start_timestamp': 1713976287714991104, 
                'end_BuyingPower': '2534489.4700', 
                'end_ExcessLiquidity': '761890.0500', 
                'end_FullAvailableFunds': '760346.8400', 
                'end_FullInitMarginReq': '8004.0200', 
                'end_FullMaintMarginReq': '6460.8000', 
                'end_FuturesPNL': '-373.7300', 
                'end_NetLiquidation': '768350.8600', 
                'end_TotalCashBalance': '766337.6224', 
                'end_UnrealizedPnL': '137.8300', 
                'end_timestamp': 1713976770533925120
            }]
        self.mock_acount = [{
                                "start_BuyingPower": "2557567.234", 
                                "currency": "USD", 
                                "start_ExcessLiquidity": "767270.345", 
                                "start_FullAvailableFunds": "767270.4837", 
                                "start_FullInitMarginReq": "282.3937", 
                                "start_FullMaintMarginReq": "282.3938", 
                                "start_FuturesPNL": "-464.883", 
                                "start_NetLiquidation": "767552.392", 
                                "start_TotalCashBalance": "-11292.332", 
                                "start_UnrealizedPnL": "0", 
                                "start_timestamp" :1712850009000000000, 
                                "end_BuyingPower": "2535588.9282", 
                                "end_ExcessLiquidity": "762034.2928", 
                                "end_FullAvailableFunds": "760676.292", 
                                "end_FullInitMarginReq": "7074.99", 
                                "end_FullMaintMarginReq": "5716.009", 
                                "end_FuturesPNL": "-487.998", 
                                "end_NetLiquidation": "767751.998", 
                                "end_TotalCashBalance": "766935.99", 
                                "end_UnrealizedPnL": "-28.99", 
                                "end_timestamp": 1712850137000000000
                            }]
        self.mock_trades =  [
                                {"timestamp": 1712850060000000000, "ticker": "HE", "quantity": "1", "cumQty": "1", "price": "91.45", "AvPrice": "91.45", "action": "SELL", "cost": "0", "currency": "USD", "fees": "2.97"}, 
                                {"timestamp": 1712850060000000000, "ticker": "ZC", "quantity": "1", "cumQty": "1", "price": "446.25", "AvPrice": "446.25", "action": "BUY", "cost": "0", "currency": "USD", "fees": "2.97"}
                            ]
        self.mock_signals =  [
                                {
                                    "timestamp": 1712850060000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": 1712850065000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": 1712850070000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }
                            ]

        self.session = LiveTradingSession(parameters = self.mock_parameters,
                                          account_data = self.mock_acount,
                                          trade_data = self.mock_trades,
                                          signal_data = self.mock_signals)

    def test_create_live_session(self):
        # test
        response =self.client.create_live_session(self.session)

        # validate
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)

    def test_get_live_session(self):
        # test
        response=self.client.get_live_sessions()

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("id", response[0])
        self.assertIn("strategy_name", response[0])
        self.assertIn("tickers", response[0])
        self.assertIn("benchmark", response[0])
        self.assertIn("data_type", response[0])
        self.assertIn("train_start", response[0])
        self.assertIn("train_end", response[0])
        self.assertIn("test_start", response[0])
        self.assertIn("test_end", response[0])
        self.assertIn("capital", response[0])
    
    def test_get_specific_session(self):
        response =self.client.create_live_session(self.session)

        # test
        response=self.client.get_specific_live_session(response['id'])

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)
        self.assertIn("price_data", response)

class TestPortfolioDataMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL)     
    
    def test_create_session(self):
        session_id = 12345

        # test
        response = self.client.create_session(session_id)

        # validation
        self.assertEqual(response, { "session_id": session_id })

        # clean up
        self.client.delete_session(session_id)

    def test_delete_session(self):
        session_id = 12345
        self.client.create_session(session_id)
        
        # test
        self.client.delete_session(session_id)

    def test_create_position(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }
        # test
        response = self.client.create_positions(session_id, data)

        # validation
        expected_data = {'action': 'BUY', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.client.delete_session(session_id)

    def test_update_position(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }
        self.client.create_positions(session_id, data)

        # test
        data['data']['action'] = "SELL"
        response = self.client.update_positions(session_id, data)

        # validation
        expected_data = {'action': 'SELL', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.client.delete_session(session_id)

    def test_get_position(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }
        self.client.create_positions(session_id, data)

        # test
        response = self.client.get_positions(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_create_order(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        # test
        response = self.client.create_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_update_order(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        self.client.create_orders(session_id, data)

        # test
        data['data']['permId'] = 100
        response = self.client.update_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_get_order(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        self.client.create_orders(session_id, data)

        # test
        response = self.client.get_orders(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_create_account(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        # test
        response = self.client.create_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_update_account(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        self.client.create_account(session_id, data)

        # test
        data['data']['FullAvailableFunds'] = 1111.99
        response = self.client.update_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_get_account(self):
        session_id = 12345
        self.client.create_session(session_id)
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        self.client.create_account(session_id, data)

        # test
        response = self.client.get_account(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)
        

if __name__ == "__main__":
    unittest.main()
