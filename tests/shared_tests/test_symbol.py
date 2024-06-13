import unittest
from midas.shared.symbol import *
from ibapi.contract import Contract
from midas.shared.orders import Action

class TestEquity(unittest.TestCase):
    def setUp(self) -> None:
        # Mock equity data
        self.ticker="AAPL"
        self.security_type=SecurityType.STOCK
        self.currency = Currency.USD  
        self.exchange = Venue.NASDAQ  
        self.fees = 0.1
        self.initial_margin = 0
        self.quantity_multiplier=1
        self.price_multiplier=1
        self.data_ticker = "AAPL2" 
        self.company_name = "Apple Inc."
        self.industry=Industry.TECHNOLOGY
        self.market_cap=10000000000.99
        self.shares_outstanding=1937476363
        self.slippage_factor=10

        # Create equity object
        self.equity_obj = Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding,
                    slippage_factor=self.slippage_factor)

    # Basic Validation
    def test_construction(self):
        # Test
        equity = Equity(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        company_name=self.company_name,
                        industry=self.industry,
                        market_cap=self.market_cap,
                        shares_outstanding=self.shares_outstanding, 
                        slippage_factor=self.slippage_factor)
        
        # Validate
        self.assertEqual(equity.ticker, self.ticker)
        self.assertIsInstance(equity.security_type, SecurityType)
        self.assertEqual(equity.data_ticker, self.data_ticker)
        self.assertEqual(equity.currency, self.currency)
        self.assertEqual(equity.exchange, self.exchange)
        self.assertEqual(equity.fees, self.fees)
        self.assertEqual(equity.initial_margin, self.initial_margin)
        self.assertEqual(equity.price_multiplier, self.price_multiplier)
        self.assertEqual(equity.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(equity.company_name, self.company_name)
        self.assertEqual(equity.industry, self.industry)
        self.assertEqual(equity.market_cap, self.market_cap)
        self.assertEqual(equity.shares_outstanding, self.shares_outstanding)
        self.assertEqual(equity.slippage_factor, self.slippage_factor)
        self.assertEqual(type(equity.contract),Contract,"contract shoudl be an instance of Contract")

    def test_commission_fees(self):
        # Test
        fees = self.equity_obj.commission_fees(5)

        # Validate
        self.assertEqual(fees, 5 * self.fees)

    def test_slippage_price_buy(self):
        current_price = 100
        
        # Test
        fees = self.equity_obj.slippage_price(current_price, action=Action.LONG)
        fees_2 = self.equity_obj.slippage_price(current_price, action=Action.COVER)

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.equity_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.equity_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_order_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.equity_obj.order_value(quantity, price)

        # Validate
        self.assertEqual(value, quantity * price)

    def test_to_dict(self):
        # Test
        equity_dict = self.equity_obj.to_dict()

        # Expected
        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'company_name': self.company_name,
                'venue': self.exchange.value,  
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
        with self.assertRaisesRegex(TypeError, "'ticker' field must be of type str."):
            Equity(ticker=1234, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)

        with self.assertRaisesRegex(TypeError, "'security_type' field must be of type SecurityType."):
            Equity(ticker=self.ticker, 
                    security_type=12345,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)

        with self.assertRaisesRegex(TypeError, "'currency' field must be enum instance Currency."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=12345, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'data_ticker' field must be a string or None."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=12345, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
        
        with self.assertRaisesRegex(TypeError, "'exchange' field must be enum instance Venue."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=2345, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'fees' field must be int or float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees="1234", 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'initial_margin' field must be an int or float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin="12345",
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'quantity_multiplier' field must be of type int or float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier="12345", 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'price_multiplier' field must be of type int or float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier="12345",
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
        
        with self.assertRaisesRegex(TypeError, "'company_name' field must be of type str."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=1234,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'industry' field must be of type Industry."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=1234,
                    market_cap=self.market_cap,
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'market_cap' field must be of type float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap="12345",
                    shares_outstanding=self.shares_outstanding)
            
        with self.assertRaisesRegex(TypeError, "'shares_outstanding' feild must be of type int."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding="12345")
            
        with self.assertRaisesRegex(TypeError, "'slippage_factor' field must be of type int or float."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor="1")

    # Value Constraints   
    def test_value_constraint(self):
        with self.assertRaisesRegex(ValueError, "'fees' field cannot be negative."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=-1, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor=1)
            
        with self.assertRaisesRegex(ValueError, "'initial_margin' field must be non-negative."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=-1,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor=1)      
              
        with self.assertRaisesRegex(ValueError, "'price_multiplier' field must be greater than zero."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=0,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor=1)
            
        with self.assertRaisesRegex(ValueError, "'quantity_multiplier' field must be greater than zero."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=0, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor=1)
    
        with self.assertRaisesRegex(ValueError, "'slippage_factor' field must be greater than zero."):
            Equity(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,
                    company_name=self.company_name,
                    industry=self.industry,
                    market_cap=self.market_cap,
                    shares_outstanding=1234, 
                    slippage_factor=-1)
            
class TestFuture(unittest.TestCase):
    def setUp(self) -> None:
        # Mock future data
        self.ticker = "HEJ4"
        self.security_type = SecurityType.FUTURE
        self.data_ticker = "HE.n.0" 
        self.currency = Currency.USD  
        self.exchange = Venue.CME  
        self.fees = 0.1
        self.initial_margin = 4000.598
        self.quantity_multiplier=40000
        self.price_multiplier=0.01
        self.product_code="HE"
        self.product_name="Lean Hogs"
        self.industry=Industry.AGRICULTURE
        self.contract_size=40000
        self.contract_units=ContractUnits.POUNDS
        self.tick_size=0.00025
        self.min_price_fluctuation=10
        self.continuous=False
        self.lastTradeDateOrContractMonth="202406"
        self.slippage_factor = 10

        # Create future object
        self.future_obj = Future(ticker=self.ticker, 
                    security_type=self.security_type,
                    data_ticker=self.data_ticker, 
                    currency=self.currency, 
                    exchange=self.exchange, 
                    fees=self.fees, 
                    initial_margin=self.initial_margin,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    product_code=self.product_code,
                    product_name=self.product_name,
                    industry=self.industry,
                    contract_size=self.contract_size,
                    contract_units=self.contract_units,
                    tick_size=self.tick_size,
                    min_price_fluctuation=self.min_price_fluctuation,
                    continuous=self.continuous, 
                    lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth, 
                    slippage_factor=self.slippage_factor)
        
    # Basic Validation
    def test_contstruction(self):
        # Test
        future = Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                        slippage_factor=self.slippage_factor)
        # Validate
        self.assertEqual(future.ticker, self.ticker)
        self.assertIsInstance(future.security_type, SecurityType)
        self.assertEqual(future.data_ticker, self.data_ticker)
        self.assertEqual(future.currency, self.currency)
        self.assertEqual(future.exchange, self.exchange)
        self.assertEqual(future.fees, self.fees)
        self.assertEqual(future.initial_margin, self.initial_margin)
        self.assertEqual(future.price_multiplier, self.price_multiplier)
        self.assertEqual(future.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(future.product_code, self.product_code)
        self.assertEqual(future.product_name, self.product_name)
        self.assertEqual(future.industry, self.industry)
        self.assertEqual(future.contract_size, self.contract_size)
        self.assertEqual(future.contract_units, self.contract_units)
        self.assertEqual(future.tick_size, self.tick_size)
        self.assertEqual(future.min_price_fluctuation, self.min_price_fluctuation)
        self.assertEqual(future.continuous, self.continuous)
        self.assertEqual(future.lastTradeDateOrContractMonth, self.lastTradeDateOrContractMonth)
        self.assertEqual(future.slippage_factor, self.slippage_factor)
        self.assertEqual(type(future.contract),Contract,"contract shoudl be an instance of Contract")

    def test_commission_fees(self):
        quantity= 10

        # Test
        fees = self.future_obj.commission_fees(quantity)

        # Validate
        self.assertEqual(fees, quantity * self.fees)

    def test_slippage_price_buy(self):
        current_price = 100
        
        # Test
        fees = self.future_obj.slippage_price(current_price, action=Action.LONG)
        fees_2 = self.future_obj.slippage_price(current_price, action=Action.COVER)

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.future_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.future_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_order_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.future_obj.order_value(quantity, price)

        # Validate
        self.assertEqual(value, quantity * self.initial_margin)

    def test_to_dict(self):        
        # Test
        future_obj_dict = self.future_obj.to_dict()

        # Expected
        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'product_code': self.product_code,
                'product_name':  self.product_name,
                'venue':  self.exchange.value,
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
        self.assertEqual(future_obj_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError, "'product_code' field must be of type str."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=1234,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError,"'product_name' field must be of type str."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=1234,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'industry' field must be of type Industry."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=1234,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'contract_size' field must be of type int or float."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size="12345",
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'contract_units' field must be of type ContractUnits."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=1234,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'tick_size' field must be of type int or float."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size="1234",
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'min_price_fluctuation' field must be of type int or float."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation="12345",
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'continuous' field must be of type boolean."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=1234, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'lastTradeDateOrContractMonth' field must be a string."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=self.tick_size,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=12345)
    
    # Value Constraint
    def test_value_cnstraints(self):
        with self.assertRaisesRegex(ValueError, "'tickSize' field must be greater than zero."):
            Future(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        product_code=self.product_code,
                        product_name=self.product_name,
                        industry=self.industry,
                        contract_size=self.contract_size,
                        contract_units=self.contract_units,
                        tick_size=0,
                        min_price_fluctuation=self.min_price_fluctuation,
                        continuous=self.continuous, 
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                        slippage_factor=1)

class TestOption(unittest.TestCase):
    def setUp(self) -> None:
        # Mock option data
        self.ticker = "AAPLP"
        self.security_type = SecurityType.OPTION
        self.data_ticker = "AAPL" 
        self.currency = Currency.USD  
        self.exchange = Venue.NASDAQ  
        self.fees = 0.1
        self.initial_margin = 0
        self.quantity_multiplier=100
        self.price_multiplier=1
        self.strike_price=109.99
        self.expiration_date="2024-01-01"
        self.option_type=Right.CALL
        self.contract_size=100
        self.underlying_name="AAPL"
        self.lastTradeDateOrContractMonth="20240201"
        self.slippage_factor = 1

        # Create option object
        self.option_obj = Option(ticker=self.ticker, 
                security_type=self.security_type,
                data_ticker=self.data_ticker, 
                currency=self.currency, 
                exchange=self.exchange, 
                fees=self.fees, 
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier, 
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor)

    # Basic Validation
    def test_contstruction(self):
        # Test
        option = Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                        slippage_factor=self.slippage_factor)
        # Validate
        self.assertEqual(option.ticker, self.ticker)
        self.assertIsInstance(option.security_type, SecurityType)
        self.assertEqual(option.data_ticker, self.data_ticker)
        self.assertEqual(option.currency, self.currency)
        self.assertEqual(option.exchange, self.exchange)
        self.assertEqual(option.fees, self.fees)
        self.assertEqual(option.initial_margin, self.initial_margin)
        self.assertEqual(option.price_multiplier, self.price_multiplier)
        self.assertEqual(option.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(option.strike_price, self.strike_price)
        self.assertEqual(option.expiration_date, self.expiration_date)
        self.assertEqual(option.option_type, self.option_type)
        self.assertEqual(option.contract_size, self.contract_size)
        self.assertEqual(option.underlying_name, self.underlying_name)
        self.assertEqual(option.lastTradeDateOrContractMonth, self.lastTradeDateOrContractMonth)
        self.assertEqual(option.slippage_factor, self.slippage_factor)
        self.assertEqual(type(option.contract),Contract,"contract shoudl be an instance of Contract")

    def test_commission_fees(self):
        quantity= 10

        # Test
        fees = self.option_obj.commission_fees(quantity)

        # Validate
        self.assertEqual(fees, quantity * self.fees)

    def test_slippage_price_buy(self):
        current_price = 100

        # Test
        fees = self.option_obj.slippage_price(current_price, action=Action.LONG)
        fees_2 = self.option_obj.slippage_price(current_price, action=Action.COVER)

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.option_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.option_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_order_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.option_obj.order_value(quantity, price)

        # Validate
        self.assertEqual(value, quantity * price * self.quantity_multiplier)

    def test_to_dict(self):
        # Test
        option_dict = self.option_obj.to_dict()
        
        # Expected
        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'strike_price': self.strike_price,
                'currency': self.currency.value, 
                'venue': self.exchange.value,
                'expiration_date': self.expiration_date,
                'option_type': self.option_type.value,
                'contract_size': self.contract_size,
                'underlying_name':self.underlying_name
            }
        }
        
        # Validate
        self.assertEqual(option_dict, expected)

    # Type Constraint
    def test_type_constraints(self):     
        with self.assertRaisesRegex(TypeError, "'strike_price' field must be of type int or float."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price="12345",
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError,"'expiration_date' field must be of type str."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=12345,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'option_type' field must be of type Right."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=self.expiration_date,
                        option_type=12345,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'contract_size' field must be of type int or float."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size="1234",
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'underlying_name' must be of type str."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=1234,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth)
            
        with self.assertRaisesRegex(TypeError, "'lastTradeDateOrContractMonth' field must be a string."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=self.strike_price,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=1234)
            
    # Value Constraint
    def test_value_constraint(self):
        with self.assertRaisesRegex(ValueError, "'strike' field must be greater than zero."):
            Option(ticker=self.ticker, 
                        security_type=self.security_type,
                        data_ticker=self.data_ticker, 
                        currency=self.currency, 
                        exchange=self.exchange, 
                        fees=self.fees, 
                        initial_margin=self.initial_margin,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,
                        strike_price=0,
                        expiration_date=self.expiration_date,
                        option_type=self.option_type,
                        contract_size=self.contract_size,
                        underlying_name=self.underlying_name,
                        lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                        slippage_factor=1)

class TestIndex(unittest.TestCase):
    def setUp(self) -> None:
        # Mock index data
        self.ticker="GSPC"
        self.security_type=SecurityType.INDEX
        self.name="S&P 500"
        self.currency=Currency.USD
        self.asset_class=AssetClass.EQUITY

        # Create index object
        self.index_obj =Index(ticker=self.ticker,
                security_type=self.security_type,
                name=self.name,
                currency=self.currency,
                asset_class=self.asset_class)

    # Basic Validation
    def test_contstruction(self):
        # Test
        index=Index(ticker=self.ticker,
                        security_type=self.security_type,
                        name=self.name,
                        currency=self.currency,
                        asset_class=self.asset_class)
        # Validate
        self.assertEqual(index.ticker, self.ticker)
        self.assertEqual(index.security_type, self.security_type)
        self.assertEqual(index.name, self.name)
        self.assertEqual(index.exchange, Venue.INDEX)
        self.assertEqual(index.currency, self.currency)
        self.assertEqual(index.asset_class, self.asset_class)

    def test_to_dict(self):
        # Test
        index_dict = self.index_obj.to_dict()
        
        # Expected
        expected = {
            'ticker': self.ticker,
            'security_type': self.security_type.value, 
            'symbol_data' : {
                'name': self.name,
                'currency': self.currency.value,
                'asset_class': self.asset_class.value,
                'venue': Venue.INDEX.value
            }
        }
        
        # Validate
        self.assertEqual(index_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError, "'name' field must be of type str."):
            Index(ticker=self.ticker,
                    security_type=self.security_type,
                    name=12345,
                    currency=self.currency,
                    asset_class=self.asset_class)
            
        with self.assertRaisesRegex(TypeError, "'asset_class' field must be of type AssetClass."):
             Index(ticker=self.ticker,
                    security_type=self.security_type,
                    name=self.name,
                    currency=self.currency,
                    asset_class=12345)
            

if __name__ == '__main__':
    unittest.main()