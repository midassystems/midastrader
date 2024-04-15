import unittest
from unittest.mock import patch, Mock
import random

from ibapi.contract import Contract
from engine.symbols.symbols import Currency, SecType, Exchange, Right, Symbol, Equity, Future, Option


#TODO: Edge case testing

class TestSymbol(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = "AAPL"
        self.valid_data_ticker = "TSLA" 
        self.valid_secType = SecType.STOCK  
        self.valid_currency = Currency.USD  
        self.valid_exchange = Exchange.NASDAQ  
        self.valid_fees = 0.1
        self.initial_margin = 0

    # Basic Validation
    def test_construction(self):
        """ Test construction with data_ticker"""
        # Constructing the Symbol instance
        symbol = Symbol(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        secType=self.valid_secType, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        initialMargin= self.initial_margin,
                        fees=self.valid_fees)
        
        self.assertEqual(symbol.ticker, self.valid_ticker)
        self.assertEqual(symbol.data_ticker, self.valid_data_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(symbol.secType, self.valid_secType)
        self.assertEqual(symbol.currency, self.valid_currency)
        self.assertEqual(symbol.fees, self.valid_fees)
        self.assertEqual(type(symbol.contract),Contract,"contract shoudl be an instance of Contract")

    def test_construction_without_data_ticker(self):
        """ Test construction without data_ticker"""
        # Constructing the Symbol instance
        symbol = Symbol(ticker=self.valid_ticker, 
                        data_ticker=None, 
                        secType=self.valid_secType, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        initialMargin= self.initial_margin,
                        fees=self.valid_fees)
        
        self.assertEqual(symbol.ticker, self.valid_ticker)
        self.assertEqual(symbol.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(symbol.secType, self.valid_secType)
        self.assertEqual(symbol.currency, self.valid_currency)
        self.assertEqual(symbol.fees, self.valid_fees)
        self.assertEqual(type(symbol.contract),Contract,"contract shoudl be an instance of Contract")

        # Constructing the Symbol instance
        symbol = Symbol(ticker=self.valid_ticker, 
                        secType=self.valid_secType, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange,
                        initialMargin= self.initial_margin, 
                        fees=self.valid_fees)
    
        self.assertEqual(symbol.ticker, self.valid_ticker)
        self.assertEqual(symbol.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(symbol.secType, self.valid_secType)
        self.assertEqual(symbol.currency, self.valid_currency)
        self.assertEqual(symbol.fees, self.valid_fees)
        self.assertEqual(type(symbol.contract),Contract,"contract shoudl be an instance of Contract")

    def test_to_contract_data(self):
        """ Test construction with data_ticker"""
        # Constructing the Symbol instance
        symbol = Symbol(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        secType=self.valid_secType, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        initialMargin= self.initial_margin,
                        fees=self.valid_fees)
        
        contract_data = symbol.to_contract_data()
        
        self.assertEqual(contract_data['symbol'], self.valid_ticker)
        self.assertEqual(contract_data["secType"], self.valid_secType.value)
        self.assertEqual(contract_data['currency'], self.valid_currency.value)
        self.assertEqual(contract_data['exchange'], self.valid_exchange.value)

    def test_to_contract(self):
        symbol = Symbol(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        secType=self.valid_secType, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        initialMargin= self.initial_margin,
                        fees=self.valid_fees)
        
        contract = symbol.to_contract()

        self.assertEqual(type(symbol.contract),Contract,"contract shoudl be an instance of Contract")
        self.assertEqual(contract.symbol,self.valid_ticker)
        self.assertEqual(contract.secType, self.valid_secType.value)
        self.assertEqual(contract.exchange, self.valid_exchange.value)
        self.assertEqual(contract.currency, self.valid_currency.value)

    # Type/Constraint Validation
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "ticker must be a string"):
            Symbol(ticker=123, 
                    data_ticker=self.valid_data_ticker, 
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    initialMargin= self.initial_margin,
                    fees=self.valid_fees)
            
    def test_data_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "data_ticker must be a string or None"):
            Symbol(ticker=self.valid_data_ticker, 
                    data_ticker=123, 
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    initialMargin= self.initial_margin,
                    fees=self.valid_fees)
            
    def test_secType_type_validation(self):
        with self.assertRaisesRegex(TypeError, "secType must be enum instance SecType"):
            Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType="self.valid_secType", 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange,
                    initialMargin= self.initial_margin, 
                    fees=self.valid_fees)
            
    def test_currency_type_validation(self):
        with self.assertRaisesRegex(TypeError,  "currency must be enum instance Currency"):
            Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType=self.valid_secType, 
                    currency="self.valid_currency", 
                    exchange=self.valid_exchange, 
                    initialMargin= self.initial_margin,
                    fees=self.valid_fees)
    
    def test_exchange_type_validation(self):
        with self.assertRaisesRegex(TypeError, "exchange must be enum instance Exchange"):
            Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange="self.valid_exchange", 
                    initialMargin= self.initial_margin,
                    fees=self.valid_fees)
            
    def test_initial_margin_type_validation(self):
        with self.assertRaisesRegex(TypeError, "initialMargin must be an int or float"):
            Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    initialMargin= "self.initial_margin",
                    fees=self.valid_fees)
            
    def test_fees_type_validation(self):
        with self.assertRaisesRegex(TypeError, "fees must be int or float"):
            Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    initialMargin= self.initial_margin,
                    fees="self.valid_fees")
        
    def test_fees_negative_constraints(self): 
        with self.assertRaisesRegex(ValueError,"fees cannot be negative"):
             Symbol(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    initialMargin= self.initial_margin,
                    fees=-0.01)
        
    # # Edge Case Validation
    # @patch('midas.symbols.Contract')
    # def test_to_contract_error_handling(self, mock_contract_class):
    #     # Configure the mock to raise an exception when any method is called
    #     mock_contract_instance = Mock()
    #     mock_contract_instance.side_effect = Exception("Unexpected error during Contract creation")
    #     mock_contract_class.return_value = mock_contract_instance

    #     # Initialize Symbol with valid parameters
    #     symbol = Symbol(ticker=self.valid_ticker,
    #                     secType=self.valid_secType,
    #                     currency=self.valid_currency,
    #                     exchange=self.valid_exchange,
    #                     fees=self.valid_fees,
    #                     data_ticker=self.valid_data_ticker)

    #     # Expect the custom logic in to_contract to handle the exception and re-raise
    #     with self.assertRaises(Exception) as context:
    #         symbol.to_contract()
        
    #     # Check that the exception message is as expected
    #     self.assertIn("Unexpected error during Contract creation", str(context.exception))

class TestEquity(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = "AAPL"
        self.valid_data_ticker = "APPL"  
        self.valid_secType = SecType.STOCK
        self.valid_currency = Currency.CAD  
        self.valid_exchange = Exchange.NYSE  
        self.valid_fees = 0.10
        self.initialMargin= 0

    # Basic Validation
    def test_construction(self):
        """ Test construction with data_ticker"""
        # Constructing the Symbol instance
        equity = Equity(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees)
        
        self.assertEqual(equity.ticker, self.valid_ticker)
        self.assertEqual(equity.data_ticker, self.valid_data_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(equity.secType, self.valid_secType)
        self.assertEqual(equity.currency, self.valid_currency)
        self.assertEqual(equity.fees, self.valid_fees)
        self.assertEqual(equity.price_multiplier, 1)
        self.assertEqual(equity.quantity_multiplier, 1)
        self.assertEqual(equity.initialMargin, 0)
        self.assertEqual(type(equity.contract),Contract,"contract shoudl be an instance of Contract")

    def test_construction_without_data_ticker(self):
        """ Test construction without data_ticker"""
        # Constructing the equity instance
        equity = Equity(ticker=self.valid_ticker, 
                        data_ticker=None, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees)
        
        self.assertEqual(equity.ticker, self.valid_ticker)
        self.assertEqual(equity.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(equity.secType, self.valid_secType)
        self.assertEqual(equity.currency, self.valid_currency)
        self.assertEqual(equity.fees, self.valid_fees)
        self.assertEqual(equity.price_multiplier, 1)
        self.assertEqual(equity.quantity_multiplier, 1)
        self.assertEqual(equity.initialMargin, 0)
        self.assertEqual(type(equity.contract),Contract,"contract shoudl be an instance of Contract")

        # Constructing the equity instance
        equity = Equity(ticker=self.valid_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees)
    
        self.assertEqual(equity.ticker, self.valid_ticker)
        self.assertEqual(equity.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(equity.secType, self.valid_secType)
        self.assertEqual(equity.currency, self.valid_currency)
        self.assertEqual(equity.fees, self.valid_fees)
        self.assertEqual(equity.price_multiplier, 1)
        self.assertEqual(equity.quantity_multiplier, 1)
        self.assertEqual(equity.initialMargin, 0)
        self.assertEqual(type(equity.contract),Contract,"contract shoudl be an instance of Contract")

    def test_to_contract_data(self):
        """ Test construction with data_ticker"""
        # Constructing the equity instance
        equity = Equity(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker,  
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees)
        
        contract_data = equity.to_contract_data()
        
        self.assertEqual(contract_data['symbol'], self.valid_ticker)
        self.assertEqual(contract_data["secType"], self.valid_secType.value)
        self.assertEqual(contract_data['currency'], self.valid_currency.value)
        self.assertEqual(contract_data['exchange'], self.valid_exchange.value)
        self.assertEqual(contract_data['multiplier'], 1)

    def test_to_contract(self):
        equity = Equity(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees)
        
        contract = equity.to_contract()

        self.assertEqual(type(equity.contract),Contract,"contract shoudl be an instance of Contract")
        self.assertEqual(contract.symbol,self.valid_ticker)
        self.assertEqual(contract.secType, self.valid_secType.value)
        self.assertEqual(contract.exchange, self.valid_exchange.value)
        self.assertEqual(contract.currency, self.valid_currency.value)
        self.assertEqual(contract.multiplier, 1)

    # Type/Constraint Validation
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "ticker must be a string"):
            Equity(ticker=123, 
                    data_ticker=self.valid_data_ticker, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees)
            
    def test_data_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "data_ticker must be a string or None"):
            Equity(ticker=self.valid_data_ticker, 
                    data_ticker=123, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees)
            
    def test_currency_type_validation(self):
        with self.assertRaisesRegex(TypeError,  "currency must be enum instance Currency"):
            Equity(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency="self.valid_currency", 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees)
    
    def test_exchange_type_validation(self):
        with self.assertRaisesRegex(TypeError, "exchange must be enum instance Exchange"):
            Equity(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange="self.valid_exchange", 
                    fees=self.valid_fees)
            
    def test_fees_type_validation(self):
        with self.assertRaisesRegex(TypeError, "fees must be int or float"):
            Equity(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees="self.valid_fees")
        
    def test_fees_negative_constraints(self): 
        with self.assertRaisesRegex(ValueError,"fees cannot be negative"):
            Equity(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=-0.01)
            
    # Edge Cases
    def test_sectype_type_validation(self):
        with self.assertRaises(TypeError):
            Equity(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker, 
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees)
            
class TestFuture(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = "HE"
        self.valid_data_ticker = "HE.n.0"  
        self.valid_secType = SecType.FUTURE
        self.valid_currency = Currency.USD  
        self.valid_exchange = Exchange.CME  
        self.valid_fees = 0.10
        self.valid_lastTradeDateOrContractMonth="202404"
        self.quantity_multiplier=40000
        self.price_multiplier=100
        self.valid_tickSize=0.00025
        self.valid_initialMargin=4564.17

    # Basic Validation
    def test_construction(self):
        """ Test construction with data_ticker"""
        # Constructing the Symbol instance
        future = Future(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees, 
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        tickSize=self.valid_tickSize,
                        initialMargin=self.valid_initialMargin)
        
        self.assertEqual(future.ticker, self.valid_ticker)
        self.assertEqual(future.data_ticker, self.valid_data_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(future.secType, self.valid_secType)
        self.assertEqual(future.currency, self.valid_currency)
        self.assertEqual(future.fees, self.valid_fees)
        self.assertEqual(future.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(future.price_multiplier, self.price_multiplier)
        self.assertEqual(future.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(future.tickSize, self.valid_tickSize)
        self.assertEqual(future.initialMargin, self.valid_initialMargin)
        self.assertEqual(type(future.contract),Contract,"contract shoudl be an instance of Contract")

    def test_construction_without_data_ticker(self):
        """ Test construction without data_ticker"""
        # Constructing the future instance
        future = Future(ticker=self.valid_ticker, 
                        data_ticker=None, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees,
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        tickSize=self.valid_tickSize,
                        initialMargin=self.valid_initialMargin)
        
        self.assertEqual(future.ticker, self.valid_ticker)
        self.assertEqual(future.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(future.secType, self.valid_secType)
        self.assertEqual(future.currency, self.valid_currency)
        self.assertEqual(future.fees, self.valid_fees)
        self.assertEqual(future.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(future.price_multiplier, self.price_multiplier)
        self.assertEqual(future.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(future.tickSize, self.valid_tickSize)
        self.assertEqual(future.initialMargin, self.valid_initialMargin)
        self.assertEqual(type(future.contract),Contract,"contract shoudl be an instance of Contract")

        # Constructing the future instance
        future = Future(ticker=self.valid_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees, 
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        tickSize=self.valid_tickSize,
                        initialMargin=self.valid_initialMargin)
    
        self.assertEqual(future.ticker, self.valid_ticker)
        self.assertEqual(future.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(future.secType, self.valid_secType)
        self.assertEqual(future.currency, self.valid_currency)
        self.assertEqual(future.fees, self.valid_fees)
        self.assertEqual(future.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(future.price_multiplier, self.price_multiplier)
        self.assertEqual(future.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(future.tickSize, self.valid_tickSize)
        self.assertEqual(future.initialMargin, self.valid_initialMargin)
        self.assertEqual(type(future.contract),Contract,"contract shoudl be an instance of Contract")

    def test_to_contract_data(self):
        """ Test construction with data_ticker"""
        # Constructing the future instance
        future = Future(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker,  
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees,
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier,  
                        tickSize=self.valid_tickSize,
                        initialMargin=self.valid_initialMargin)
                        
        
        contract_data = future.to_contract_data()
        
        self.assertEqual(contract_data['symbol'], self.valid_ticker)
        self.assertEqual(contract_data["secType"], self.valid_secType.value)
        self.assertEqual(contract_data['currency'], self.valid_currency.value)
        self.assertEqual(contract_data['exchange'], self.valid_exchange.value)
        self.assertEqual(contract_data["lastTradeDateOrContractMonth"], self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(contract_data['multiplier'], self.quantity_multiplier)

    def test_to_contract(self):
        future = Future(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees, 
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        tickSize=self.valid_tickSize,
                        initialMargin=self.valid_initialMargin)
                        
        
        contract = future.to_contract()

        self.assertEqual(type(future.contract),Contract,"contract shoudl be an instance of Contract")
        self.assertEqual(contract.symbol,self.valid_ticker)
        self.assertEqual(contract.secType, self.valid_secType.value)
        self.assertEqual(contract.exchange, self.valid_exchange.value)
        self.assertEqual(contract.currency, self.valid_currency.value)
        self.assertEqual(contract.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(contract.multiplier, self.quantity_multiplier)

    # Type/Constraint Validation
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "ticker must be a string"):
            Future(ticker=123, 
                    data_ticker=self.valid_data_ticker, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees,
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
    def test_data_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "data_ticker must be a string or None"):
            Future(ticker=self.valid_data_ticker, 
                    data_ticker=123, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)

    def test_currency_type_validation(self):
        with self.assertRaisesRegex(TypeError,  "currency must be enum instance Currency"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency="self.valid_currency", 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees,                         
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
    
    def test_exchange_type_validation(self):
        with self.assertRaisesRegex(TypeError, "exchange must be enum instance Exchange"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange="self.valid_exchange", 
                    fees=self.valid_fees,
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
                
    def test_fees_type_validation(self):
        with self.assertRaisesRegex(TypeError, "fees must be int or float"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees="self.valid_fees", 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
        
    def test_lastTradeDateOrContractMonth_type_validation(self):
        with self.assertRaisesRegex(TypeError, "lastTradeDateOrContractMonth must be a string"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=202412,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
        
    def test_multiplier_type_validation(self):
        with self.assertRaisesRegex(TypeError,"multiplier must be a int"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier="self.valid_multiplier", 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
    def test_tickSize_type_validation(self):
        with self.assertRaisesRegex(TypeError, "tickSize must be a int or float"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize="self.valid_tickSize",
                    initialMargin=self.valid_initialMargin)
            
    def test_initialMargin_type_validation(self):
        with self.assertRaisesRegex(TypeError, "initialMargin must be an int or float"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin="self.valid_initialMargin")
    
    def test_quantity_multiplier_constraint(self):
        with self.assertRaisesRegex(ValueError,"quantity_multiplier must be greater than 0"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=0, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
    def test_tickSize_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"tickSize must be greater than 0"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=-0.01, 
                    initialMargin=self.valid_initialMargin)

    def test_initialMargin_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"initialMargin must be non-negative"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=-0.9)
            
    def test_price_multiplier_constraint(self):
        with self.assertRaisesRegex(ValueError, "price_multiplier must be greater than 0"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    price_multiplier=0, 
                    quantity_multiplier=1, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
    def test_tickSize_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"tickSize must be greater than 0"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=0,
                    initialMargin=self.valid_initialMargin)

    def test_fees_negative_constraints(self): 
        with self.assertRaisesRegex(ValueError,"fees cannot be negative"):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=-0.01, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,  
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
    # Edge Cases
    def test_sectype_type_validation(self):
        with self.assertRaises(TypeError):
            Future(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker, 
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    tickSize=self.valid_tickSize,
                    initialMargin=self.valid_initialMargin)
            
class TestOption(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = "AAPL"
        self.valid_data_ticker = "AAPL2"  
        self.valid_secType = SecType.OPTION
        self.valid_currency = Currency.USD  
        self.valid_exchange = Exchange.NASDAQ 
        self.valid_fees = 0.10
        self.valid_lastTradeDateOrContractMonth="20240412" #'YYYYMMDD'
        self.quantity_multiplier=100
        self.price_multiplier=1
        self.valid_right = random.choice([Right.CALL,Right.PUT])
        self.valid_strike = 105.0
        self.initialMargin = 0

    # Basic Validation
    def test_construction(self):
        option = Option(ticker=self.valid_ticker,
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees, 
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        right= self.valid_right, 
                        strike=self.valid_strike,
                        initialMargin=self.initialMargin
                        )
        
        self.assertEqual(option.ticker, self.valid_ticker)
        self.assertEqual(option.data_ticker, self.valid_data_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(option.secType, self.valid_secType)
        self.assertEqual(option.currency, self.valid_currency)
        self.assertEqual(option.fees, self.valid_fees)
        self.assertEqual(option.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(option.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(option.price_multiplier, self.price_multiplier)
        self.assertEqual(option.right, self.valid_right)
        self.assertEqual(option.strike, self.valid_strike)
        self.assertEqual(type(option.contract),Contract,"contract shoudl be an instance of Contract")
    
    def test_construction_without_data_ticker(self):
        """ Test construction without data_ticker"""
        # Constructing the option instance
        option = Option(ticker=self.valid_ticker, 
                        data_ticker=None, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees,                     
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        right= self.valid_right, 
                        initialMargin=self.initialMargin,
                        strike=self.valid_strike)
        
        self.assertEqual(option.ticker, self.valid_ticker)
        self.assertEqual(option.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(option.secType, self.valid_secType)
        self.assertEqual(option.currency, self.valid_currency)
        self.assertEqual(option.fees, self.valid_fees)
        self.assertEqual(option.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(option.price_multiplier, self.price_multiplier)
        self.assertEqual(type(option.contract),Contract,"contract shoudl be an instance of Contract")

        # Constructing the option instance
        option = Option(ticker=self.valid_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees,
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        right= self.valid_right, 
                        initialMargin=self.initialMargin,
                        strike=self.valid_strike)
    
        self.assertEqual(option.ticker, self.valid_ticker)
        self.assertEqual(option.data_ticker, self.valid_ticker, "data_ticker should default to ticker if None is provided.")
        self.assertEqual(option.secType, self.valid_secType)
        self.assertEqual(option.currency, self.valid_currency)
        self.assertEqual(option.fees, self.valid_fees)
        self.assertEqual(option.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(option.price_multiplier, self.price_multiplier)
        self.assertEqual(type(option.contract),Contract,"contract shoudl be an instance of Contract")

    def test_to_contract_data(self):
        """ Test construction with data_ticker"""
        # Constructing the option instance
        option = Option(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees,                       
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        right= self.valid_right, 
                        strike=self.valid_strike,
                        initialMargin=self.initialMargin
                        )
        
        contract_data = option.to_contract_data()
        
        self.assertEqual(contract_data['symbol'], self.valid_ticker)
        self.assertEqual(contract_data["secType"], self.valid_secType.value)
        self.assertEqual(contract_data['currency'], self.valid_currency.value)
        self.assertEqual(contract_data['exchange'], self.valid_exchange.value)
        self.assertEqual(contract_data["lastTradeDateOrContractMonth"], self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(contract_data['multiplier'], self.quantity_multiplier)
        self.assertEqual(contract_data["right"], self.valid_right.value) # Assuming Right is an Enum
        self.assertEqual(contract_data["strike"], self.valid_strike)

    def test_to_contract(self):
        option = Option(ticker=self.valid_ticker, 
                        data_ticker=self.valid_data_ticker, 
                        currency=self.valid_currency, 
                        exchange=self.valid_exchange, 
                        fees=self.valid_fees, 
                        lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                        quantity_multiplier=self.quantity_multiplier, 
                        price_multiplier=self.price_multiplier, 
                        right= self.valid_right, 
                        strike=self.valid_strike,
                        initialMargin=self.initialMargin
                        )
        
        contract = option.to_contract()

        self.assertEqual(type(option.contract),Contract,"contract shoudl be an instance of Contract")
        self.assertEqual(contract.symbol,self.valid_ticker)
        self.assertEqual(contract.secType, self.valid_secType.value)
        self.assertEqual(contract.exchange, self.valid_exchange.value)
        self.assertEqual(contract.currency, self.valid_currency.value)
        self.assertEqual(contract.lastTradeDateOrContractMonth, self.valid_lastTradeDateOrContractMonth)
        self.assertEqual(contract.right, self.valid_right.value)
        self.assertEqual(contract.strike, self.valid_strike)

    # Type/Constraint Validation
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "ticker must be a string"):
            Option(ticker=123, 
                    data_ticker=self.valid_data_ticker, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees,
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    def test_data_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError, "data_ticker must be a string or None"):
            Option(ticker=self.valid_data_ticker, 
                    data_ticker=123, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)

    def test_currency_type_validation(self):
        with self.assertRaisesRegex(TypeError,  "currency must be enum instance Currency"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency="self.valid_currency", 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees,                         
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
    
    def test_exchange_type_validation(self):
        with self.assertRaisesRegex(TypeError, "exchange must be enum instance Exchange"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange="self.valid_exchange", 
                    fees=self.valid_fees,
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
                
    def test_fees_type_validation(self):
        with self.assertRaisesRegex(TypeError, "fees must be int or float"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees="self.valid_fees", 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
        
    def test_lastTradeDateOrContractMonth_type_validation(self):
        with self.assertRaisesRegex(TypeError, "lastTradeDateOrContractMonth must be a string"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=20241215,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,  
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
        
    def test_multiplier_type_validation(self):
        with self.assertRaisesRegex(TypeError,"quantity_multiplier must be a int"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier="self.valid_multiplier", 
                    price_multiplier=self.price_multiplier,  
                    right= self.valid_right, 
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    def test_right_type_validation(self):
        with self.assertRaisesRegex(TypeError, "right must be an instance of Right"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right="self.valid_right",
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    def test_strike_type_validation(self):
        with self.assertRaisesRegex(TypeError, "strike must be an int or float"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,  
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike="self.valid_strike")
    
    def test_multiplier_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"multiplier must be greater than 0"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=-1, 
                    price_multiplier=1, 
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    def test_strike_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"strike must be greater than 0"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike=-0.01)
            
    def test_multiplier_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "quantity_multiplier must be greater than 0"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=0,
                    price_multiplier=1, 
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    def test_strike_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"strike must be greater than 0"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike=0)

    def test_fees_negative_constraints(self): 
        with self.assertRaisesRegex(ValueError,"fees cannot be negative"):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker,
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=-0.01, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier,  
                    right=self.valid_right,
                    initialMargin=self.initialMargin,
                    strike=self.valid_strike)
            
    # Edge Cases
    def test_sectype_type_validation(self):
        with self.assertRaises(TypeError):
            Option(ticker=self.valid_ticker, 
                    data_ticker=self.valid_data_ticker, 
                    secType=self.valid_secType, 
                    currency=self.valid_currency, 
                    exchange=self.valid_exchange, 
                    fees=self.valid_fees, 
                    lastTradeDateOrContractMonth=self.valid_lastTradeDateOrContractMonth,
                    quantity_multiplier=self.quantity_multiplier, 
                    price_multiplier=self.price_multiplier, 
                    right=self.valid_right,
                    strike=self.valid_strike)


if __name__ == '__main__':
    unittest.main()