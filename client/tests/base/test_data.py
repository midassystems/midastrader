import unittest
from decimal import Decimal
from client.base.data import *

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
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "open": self.open,
            "close": self.close,
            "high": self.high,
            "low": self.low, 
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
          
if __name__ =="__main__":
    unittest.main()