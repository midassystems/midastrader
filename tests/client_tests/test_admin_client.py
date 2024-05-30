import copy
import logging
import unittest
from decimal import Decimal
from decouple import config

from midas.client import DatabaseClient
from midas.client import AdminDatabaseClient

from midas.shared.market_data import *
from midas.shared.backtest import Backtest
from midas.shared.live_session import LiveTradingSession
from midas.shared.symbol import Symbol, Equity, SecurityType, Currency, Future, Option, Index, AssetClass, ContractUnits, Venue, Industry, Right


DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

class TestSymbolDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = AdminDatabaseClient(DATABASE_KEY, DATABASE_URL) 

    @classmethod
    def tearDownClass(cls):
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
                    except Exception as e:
                        pass
            except Exception as e:
                pass

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
        cls.client = AdminDatabaseClient(DATABASE_KEY, DATABASE_URL) 

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
                    except Exception as e:
                        pass
            except Exception as e:
                pass

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

        # clean up
        self.client.delete_symbol(response["id"])

    def test_create_symbol_future(self):
        # test 
        response = self.client.create_symbol(self.future)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.future.ticker)
        
        # clean up
        self.client.delete_symbol(response["id"])

    def test_create_symbol_option(self):
        # test 
        response = self.client.create_symbol(self.option)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.option.ticker)
        
        # clean up
        self.client.delete_symbol(response["id"])

    def test_create_symbol_index(self):
        # test 
        response = self.client.create_symbol(self.index)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.index.ticker)
        
        # clean up
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
        cls.client = AdminDatabaseClient(DATABASE_KEY, DATABASE_URL) 
        cls.user = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
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
                    except Exception as e:
                        pass
            except Exception as e:
                pass

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
        old_bar=self.user.get_bar_data(tickers, start_date, end_date)[0]

        new_bar = copy.deepcopy(self.bar)
        new_bar.open = Decimal("0.0009")

        # test
        response=self.client.update_bar_data(old_bar['id'], new_bar)

        # validate
        self.assertEqual(old_bar['id'], response['id'])
        self.assertEqual(Decimal(response['open']), new_bar.open)


if __name__ == "__main__":
    unittest.main()
