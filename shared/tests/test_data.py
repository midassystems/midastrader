import unittest
from unittest.mock import Mock, patch
from contextlib import ExitStack
from decimal import Decimal
from shared.data import *

class TestSymbol(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker = "AAPL"
        self.security_type = SecurityType.STOCK

    # Basic Validation  
    def test_construction_valid(self):
        # Test
        symbol = Symbol(self.ticker, self.security_type)

        # Validate
        self.assertEqual(symbol.ticker, self.ticker)
        self.assertIsInstance(symbol.security_type, SecurityType)

    def test_to_dict(self):
        symbol = Symbol(self.ticker, self.security_type)
        
        # Test
        symbol_dict = symbol.to_dict()

        # Validate
        self.assertEqual(symbol_dict['ticker'], self.ticker)
        self.assertEqual(symbol_dict['security_type'], self.security_type.value)


    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            Symbol(1234, self.security_type)

        with self.assertRaisesRegex(TypeError,"security_type must be of type SecurityType."):
            Symbol(self.ticker, "STOCK")

class TestEquity(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="AAPL"
        self.security_type=SecurityType.STOCK
        self.company_name = "Apple Inc."
        self.venue=Venue.NASDAQ
        self.currency=Currency.USD
        self.industry=Industry.TECHNOLOGY
        self.market_cap=10000000000.99
        self.shares_outstanding=1937476363

    # Basic Validation
    def test_contstruction(self):
        # Test
        equity = Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
        # Validate
        self.assertEqual(equity.ticker, self.ticker)
        self.assertEqual(equity.security_type, self.security_type)
        self.assertEqual(equity.company_name, self.company_name)
        self.assertEqual(equity.venue, self.venue)
        self.assertEqual(equity.currency, self.currency)
        self.assertEqual(equity.industry, self.industry)
        self.assertEqual(equity.market_cap, self.market_cap)
        self.assertEqual(equity.shares_outstanding, self.shares_outstanding)

    def test_to_dict(self):
        equity = Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
        # Test
        equity_dict = equity.to_dict()

        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'company_name': self.company_name,
                'venue': self.venue.value,  
                'currency': self.currency.value,  
                'industry': self.industry.value,  
                'market_cap': self.market_cap,
                'shares_outstanding': self.shares_outstanding
                }
        }
        
        # Validate
        self.assertEqual(equity_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            Equity(ticker=123,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)

        with self.assertRaisesRegex(TypeError,"security_type must be of type SecurityType."):
            Equity(ticker=self.ticker,
                        security_type="self.security_type",
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError,"company_name must be of type str"):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=1234,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "venue must be of type Venue."):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue="self.venue",
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "currency must be of type Currency."):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency="self.currency",
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "industry must be of type Industry."):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry="self.industry",
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "market_cap must be of type float."):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap="self.market_cap",
                        shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError,"shares_outstanding must be of type int."):
            Equity(ticker=self.ticker,
                        security_type=self.security_type,
                        company_name=self.company_name,
                        venue=self.venue,
                        currency=self.currency,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding="self.shares_outstanding")
            
class TestFuture(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker = "HEJ4"
        self.security_type = SecurityType.FUTURE
        self.product_code="HE"
        self.product_name="Lean Hogs"
        self.venue=Venue.CME
        self.currency=Currency.USD
        self.industry=Industry.AGRICULTURE
        self.contract_size=40000
        self.contract_units=ContractUnits.POUNDS
        self.tick_size=0.00025
        self.min_price_fluctuation=10
        self.continuous=False

    # Basic Validation
    def test_contstruction(self):
        # Test
        future=Future(ticker=self.ticker,
                      security_type=self.security_type,
                      product_code=self.product_code,
                      product_name=self.product_name,
                      venue=self.venue,
                      currency=self.currency,
                      industry=self.industry,
                      contract_size=self.contract_size,
                      contract_units=self.contract_units,
                      tick_size=self.tick_size,
                      min_price_fluctuation=self.min_price_fluctuation,
                      continuous=self.continuous)
        # Validate
        self.assertEqual(future.ticker, self.ticker)
        self.assertEqual(future.security_type, self.security_type)
        self.assertEqual(future.product_code, self.product_code)
        self.assertEqual(future.product_name, self.product_name)
        self.assertEqual(future.venue, self.venue)
        self.assertEqual(future.currency, self.currency)
        self.assertEqual(future.industry, self.industry)
        self.assertEqual(future.contract_size, self.contract_size)
        self.assertEqual(future.contract_units, self.contract_units)
        self.assertEqual(future.tick_size, self.tick_size)
        self.assertEqual(future.min_price_fluctuation, self.min_price_fluctuation)
        self.assertEqual(future.continuous, self.continuous)

    def test_to_dict(self):
        future=Future(ticker=self.ticker,
                      security_type=self.security_type,
                      product_code=self.product_code,
                      product_name=self.product_name,
                      venue=self.venue,
                      currency=self.currency,
                      industry=self.industry,
                      contract_size=self.contract_size,
                      contract_units=self.contract_units,
                      tick_size=self.tick_size,
                      min_price_fluctuation=self.min_price_fluctuation,
                      continuous=self.continuous)
        # Test
        future_dict = future.to_dict()

        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'product_code': self.product_code,
                'product_name':  self.product_name,
                'venue':  self.venue.value,
                'currency': self.currency.value,
                'industry': self.industry.value,
                'contract_size': self.contract_size,
                'contract_units': self.contract_units.value,
                'tick_size': self.tick_size,
                'min_price_fluctuation' : self.min_price_fluctuation,
                'continuous' : self.continuous
                }
        }
        
        # Validate
        self.assertEqual(future_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            Future(ticker=1234,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)

        with self.assertRaisesRegex(TypeError,"security_type must be of type SecurityType."):
            Future(ticker=self.ticker,
                                security_type="self.security_type",
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError, "venue must be of type Venue."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue="self.venue",
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError, "currency must be of type Currency."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency="self.currency",
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError, "industry must be of type Industry."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=1234,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError, "contract_size must be of type int or float."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size="self.contract_size",
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError, "contract_units must be of type ContractUnits."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=1234,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError,"tick_size must be of type int or float."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size="1234",
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous=self.continuous)
            
        with self.assertRaisesRegex(TypeError,"min_price_fluctuation must be of type int or float."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation="self.min_price_fluctuation,",
                                continuous=self.continuous)
        
        with self.assertRaisesRegex(TypeError,"continuous must be of type boolean."):
            Future(ticker=self.ticker,
                                security_type=self.security_type,
                                product_code=self.product_code,
                                product_name=self.product_name,
                                venue=self.venue,
                                currency=self.currency,
                                industry=self.industry,
                                contract_size=self.contract_size,
                                contract_units=self.contract_units,
                                tick_size=self.tick_size,
                                min_price_fluctuation=self.min_price_fluctuation,
                                continuous="true")
            
class TestOption(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker = "AAPL"
        self.security_type = SecurityType.OPTION
        self.strike_price=109.99
        self.currency=Currency.USD
        self.venue=Venue.NASDAQ
        self.expiration_date="2024-01-01"
        self.option_type="CALL"
        self.contract_size=100
        self.underlying_name="AAPL Inc"

    # Basic Validation
    def test_contstruction(self):
        # Test
        option=Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
        # Validate
        self.assertEqual(option.ticker, self.ticker)
        self.assertEqual(option.security_type, self.security_type)
        self.assertEqual(option.currency, self.currency)
        self.assertEqual(option.venue, self.venue)
        self.assertEqual(option.expiration_date, self.expiration_date)
        self.assertEqual(option.contract_size, self.contract_size)
        self.assertEqual(option.option_type, self.option_type)
        self.assertEqual(option.underlying_name, self.underlying_name)

    def test_to_dict(self):
        option=Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
        # Test
        option_dict = option.to_dict()

        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'strike_price': self.strike_price,
                'currency': self.currency.value, 
                'venue': self.venue.value,
                'expiration_date': self.expiration_date,
                'option_type': self.option_type,
                'contract_size': self.contract_size,
                'underlying_name':self.underlying_name
            }
        }
        
        # Validate
        self.assertEqual(option_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            Option(ticker=1234,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)

        with self.assertRaisesRegex(TypeError,"security_type must be of type SecurityType."):
            Option(ticker=self.ticker,
                        security_type="self.security_type,",
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
            
        with self.assertRaisesRegex(TypeError, "venue must be of type Venue."):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue="self.venue",
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
            
        with self.assertRaisesRegex(TypeError, "currency must be of type Currency."):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency="self.currency",
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
            
        with self.assertRaisesRegex(TypeError, "expiration_date must be of type str"):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=12345,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
            
        with self.assertRaisesRegex(TypeError, "option_type must be of type str"):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=12345,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name)
        
        with self.assertRaisesRegex(TypeError, "contract_size must be of type int or float"):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size="self.contract_size",
                        underlying_name=self.underlying_name)
            
        with self.assertRaisesRegex(TypeError,"underlying_name must be of type str"):
            Option(ticker=self.ticker,
                        security_type=self.security_type,
                        strike_price=self.strike_price,
                        currency=self.currency,
                        venue=self.venue,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=1234)
            
class TestIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="GSPC"
        self.security_type=SecurityType.INDEX
        self.name="S&P 500"
        self.currency=Currency.USD
        self.asset_class=AssetClass.EQUITY
        self.venue= Venue.NASDAQ

    # Basic Validation
    def test_contstruction(self):
        # Test
        index=Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class=self.asset_class)
        # Validate
        self.assertEqual(index.ticker, self.ticker)
        self.assertEqual(index.security_type, self.security_type)
        self.assertEqual(index.name, self.name)
        self.assertEqual(index.venue, self.venue)
        self.assertEqual(index.currency, self.currency)
        self.assertEqual(index.asset_class, self.asset_class)

    def test_to_dict(self):
        index=Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class=self.asset_class)
        # Test
        index_dict = index.to_dict()

        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'name': self.name,
                'currency': self.currency.value,
                'asset_class': self.asset_class.value,
                'venue': self.venue.value
            }
        }
        
        # Validate
        self.assertEqual(index_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            Index(ticker=1234,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class=self.asset_class)
        
        with self.assertRaisesRegex(TypeError,"security_type must be of type SecurityType."):
            Index(ticker=self.ticker,
                        security_type="self.security_type",
                        name=self.name,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class=self.asset_class)
            
        with self.assertRaisesRegex(TypeError,"name must be of type str"):
            Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=1234,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class=self.asset_class)
            
        with self.assertRaisesRegex(TypeError, "venue must be of type Venue."):
            Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        venue="self.venue",
                        asset_class=self.asset_class)
            
        with self.assertRaisesRegex(TypeError, "currency must be of type Currency."):
            Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency="self.currency",
                        venue=self.venue,
                        asset_class=self.asset_class)
            
        with self.assertRaisesRegex(TypeError, "asset_class must be of type AssetClass."):
            Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        venue=self.venue,
                        asset_class="self.asset_class")
            
class TestBarData(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="AAPL"   
        self.timestamp="2024-01-01"
        self.open=Decimal(100.990808)
        self.high=Decimal(1111.9998)
        self.low=Decimal(99.990898)
        self.close=Decimal(105.9089787)
        self.volume=100000909
    
    # Basic Validation
    def test_construction(self):
        # test
        bar = BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
        # Validate
        self.assertEqual(bar.ticker,self.ticker)
        self.assertEqual(bar.timestamp,self.timestamp)
        self.assertEqual(bar.open,self.open)
        self.assertEqual(bar.high,self.high)
        self.assertEqual(bar.low,self.low)
        self.assertEqual(bar.close,self.close)
        self.assertEqual(bar.volume,self.volume)

    def test_to_dict(self):
        bar = BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
        # test
        bar_dict = bar.to_dict()

        expected = {
            "symbol": self.ticker,
            "timestamp": self.timestamp,
            "open": str(self.open),
            "close": str(self.close),
            "high": str(self.high),
            "low": str(self.low), 
            "volume": self.volume
        }

        # Validate
        self.assertEqual(bar_dict, expected)

    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            BarData(ticker=1234,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
            
        with self.assertRaisesRegex(TypeError,"timestamp must be of type str" ):
            BarData(ticker=self.ticker,
                      timestamp=123456,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
        
        with self.assertRaisesRegex(TypeError,"open must be of type Decimal." ):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=12345,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
            
        with self.assertRaisesRegex(TypeError, "high must be of type Decimal."):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=12345,
                      low=self.low,
                      close=self.close,
                      volume=self.volume)
            
        with self.assertRaisesRegex(TypeError, "low must be of type Decimal."):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=1234,
                      close=self.close,
                      volume=self.volume)

        with self.assertRaisesRegex(TypeError, "close must be of type Decimal."):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=12345,
                      volume=self.volume)
            
        with self.assertRaisesRegex(TypeError,"volume must be of type int."):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume="123456")
              
class TestQuoteData(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="AAPL"   
        self.timestamp="2024-01-01"
        self.ask=Decimal(34.989889)
        self.ask_size=Decimal(2232.323232)
        self.bid=Decimal(12.34456)
        self.bid_size=Decimal(112.234345)

    # Basic Validation
    def test_construction(self):
        # test
        tbbo = QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
        # Validate
        self.assertEqual(tbbo.ticker,self.ticker)
        self.assertEqual(tbbo.timestamp,self.timestamp)
        self.assertEqual(tbbo.ask,self.ask)
        self.assertEqual(tbbo.ask_size,self.ask_size)
        self.assertEqual(tbbo.bid,self.bid)
        self.assertEqual(tbbo.bid_size,self.bid_size)

    def test_to_dict(self):
        tbbo = QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
        # test
        tbbo_dict = tbbo.to_dict()

        expected = {
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "ask": self.ask,
            "ask_size": self.ask_size,
            "bid": self.bid,
            "bid_size": self.bid_size 
        }

        # Validate
        self.assertEqual(tbbo_dict, expected)

    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError,"ticker must be of type str"):
            QuoteData(ticker=1234,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
            
        with self.assertRaisesRegex(TypeError,"timestamp must be of type str" ):
            QuoteData(ticker=self.ticker,
                      timestamp=123456,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
        
        with self.assertRaisesRegex(TypeError,"'ask' must be of type Decimal"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask="1234",
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
            
        with self.assertRaisesRegex(TypeError, "'ask_size' must be of type Decimal"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                       ask=self.ask,
                      ask_size="12345",
                      bid=self.bid,
                      bid_size=self.bid_size)
            
        with self.assertRaisesRegex(TypeError, "'bid' must be of type Decimal"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid="1234",
                      bid_size=self.bid_size)

        with self.assertRaisesRegex(TypeError, "'bid_size' must be of type Decimal"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size="self.bid_size")
            
    def test_value_constraints(self):
        with self.assertRaisesRegex(ValueError,"'ask' must be greater than zero"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=Decimal(0),
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=self.bid_size)
            
        with self.assertRaisesRegex(ValueError,"'ask_size' must be greater than zero"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=Decimal(0),
                      bid=self.bid,
                      bid_size=self.bid_size)
        
        with self.assertRaisesRegex(ValueError,"'bid' must be greater than zero"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      ask=self.ask,
                      ask_size=self.ask_size,
                      bid=Decimal(0),
                      bid_size=self.bid_size)
            
        with self.assertRaisesRegex(ValueError, "'bid_size' must be greater than zero"):
            QuoteData(ticker=self.ticker,
                      timestamp=self.timestamp,
                       ask=self.ask,
                      ask_size=self.ask_size,
                      bid=self.bid,
                      bid_size=Decimal(0))
          
class TestBacktest(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": "2018-05-18", 
                                "train_end": "2023-01-19", 
                                "test_start": "2023-01-19", 
                                "test_end": "2024-01-19", 
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
                                    "timestamp": "2023-12-09T12:00:00Z",
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": "2023-12-10T12:00:00Z",
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
                                "timestamp": "2023-01-03T00:00:00+0000", 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "price": 130.74, 
                                "cost": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.mock_signals =  [{
                                "timestamp": "2023-01-03T00:00:00+0000", 
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

    # Basic Validation
    def test_to_dict(self):
        backtest_dict = self.backtest.to_dict()

        self.assertEqual(backtest_dict['parameters'], self.mock_parameters)
        self.assertEqual(backtest_dict['static_stats'], self.mock_static_stats)
        self.assertEqual(backtest_dict['timeseries_stats'], self.mock_timeseries_stats)
        self.assertEqual(backtest_dict['regression_stats'], self.mock_regression_stats)
        self.assertEqual(backtest_dict['signals'], self.mock_signals)
        self.assertEqual(backtest_dict['trades'], self.mock_trades)

    def test_type_constraints(self):
        with self.assertRaisesRegex(ValueError, "parameters must be a dictionary"):
            Backtest(parameters = "self.mock_parameters,",
                                static_stats = self.mock_static_stats,
                                regression_stats=self.mock_regression_stats,
                                timeseries_stats = self.mock_timeseries_stats,
                                trade_data = self.mock_trades,
                                signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError,"static_stats must be a list of dictionaries" ):
            Backtest(parameters = self.mock_parameters,
                                static_stats = "self.mock_static_stats",
                                regression_stats=self.mock_regression_stats,
                                timeseries_stats = self.mock_timeseries_stats,
                                trade_data = self.mock_trades,
                                signal_data = self.mock_signals)
        with self.assertRaisesRegex(ValueError,"regression_stats must be a list of dictionaries" ):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats="self.mock_regression_stats",
                                 timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "timeseries_stats must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats=self.mock_regression_stats,
                                 timeseries_stats = "self.mock_timeseries_stats",
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "trade_data must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats=self.mock_regression_stats,
                                 timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = "self.mock_trades",
                                 signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "signal_data must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats=self.mock_regression_stats,
                                 timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = "self.mock_signals")

class TestLiveTradingSession(unittest.TestCase):    
    def setUp(self) -> None:
        
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": "2020-05-18", 
                                "train_end": "2024-01-01", 
                                "test_start": "2024-01-02", 
                                "test_end": "2024-01-19", 
                                "tickers": ["HE", "ZC"], 
                                "benchmark": ["^GSPC"]
                            }
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
                                "start_timestamp": "2024-04-11T11:40:09.861731", 
                                "end_BuyingPower": "2535588.9282", 
                                "end_ExcessLiquidity": "762034.2928", 
                                "end_FullAvailableFunds": "760676.292", 
                                "end_FullInitMarginReq": "7074.99", 
                                "end_FullMaintMarginReq": "5716.009", 
                                "end_FuturesPNL": "-487.998", 
                                "end_NetLiquidation": "767751.998", 
                                "end_TotalCashBalance": "766935.99", 
                                "end_UnrealizedPnL": "-28.99", 
                                "end_timestamp": "2024-04-11T11:42:17.046984"
                            }]
        self.mock_trades =  [
                                {"timestamp": "2024-04-11T15:41:00+00:00", "ticker": "HE", "quantity": "1", "cumQty": "1", "price": "91.45", "AvPrice": "91.45", "action": "SELL", "cost": "0", "currency": "USD", "fees": "2.97"}, 
                                {"timestamp": "2024-04-11T15:41:00+00:00", "ticker": "ZC", "quantity": "1", "cumQty": "1", "price": "446.25", "AvPrice": "446.25", "action": "BUY", "cost": "0", "currency": "USD", "fees": "2.97"}
                            ]
        self.mock_signals =  [
                                {
                                    "timestamp": "2024-04-11T15:41:00+00:00", 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": "2024-04-11T15:41:05+00:00", 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": "2024-04-11T15:41:10+00:00", 
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

    # Basic Validation
    def test_to_dict_valid(self):
        session_dict = self.session.to_dict()

        self.assertEqual(session_dict['parameters'], self.mock_parameters)
        self.assertEqual(session_dict['account_data'], self.mock_acount)
        self.assertEqual(session_dict['signals'], self.mock_signals)
        self.assertEqual(session_dict['trades'], self.mock_trades)

    def test_type_constraints(self):
        with self.assertRaisesRegex(ValueError, "parameters must be a dictionary"):
            LiveTradingSession(parameters = "self.mock_parameters,",
                                          account_data = self.mock_acount,
                                          trade_data = self.mock_trades,
                                          signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError,"trade_data must be a list of dictionaries" ):
            LiveTradingSession(parameters = self.mock_parameters,
                                        account_data = self.mock_acount,
                                        trade_data = "self.mock_trades",
                                        signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError,"account_data must be a list of dictionaries" ):
            LiveTradingSession(parameters = self.mock_parameters,
                                        account_data = "self.mock_acount",
                                        trade_data = self.mock_trades,
                                        signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "signal_data must be a list of dictionaries"):
            LiveTradingSession(parameters = self.mock_parameters,
                                        account_data = self.mock_acount,
                                        trade_data = self.mock_trades,
                                        signal_data = "self.mock_signals")
            

if __name__ =="__main__":
    unittest.main()