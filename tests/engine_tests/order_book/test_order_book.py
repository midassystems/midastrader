import unittest
import numpy as np
from decimal import Decimal
from unittest.mock import Mock
from midas.engine.events import MarketEvent
from midas.engine.order_book import OrderBook
from midas.engine.observer import EventType, Observer, Subject
from midas.shared.market_data import BarData, QuoteData, MarketDataType, MarketData

class ChildObserver(Observer):
    def __init__(self) -> None:
        self.tester = None

    def update(self, subject, event_type: EventType):
        if event_type == EventType.POSITION_UPDATE:
            self.tester = 1
        elif event_type == EventType.ORDER_UPDATE:
            self.tester = 2
        elif event_type == EventType.ACCOUNT_DETAIL_UPDATE:
            self.tester = 3
        elif event_type == EventType.MARKET_EVENT:
            self.tester = 4
        elif event_type == EventType.RISK_MODEL_UPDATE:
            self.tester = 5

class TestOrderBook(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.mock_event_queue = Mock()
        self.timestamp = np.uint64(1707221160000000000)
        self.ticker="AAPL"
        
        # Test bardata orderbook
        self.valid_bardata_order_book = OrderBook(MarketDataType.BAR, self.mock_event_queue)
        self.valid_bar = BarData(ticker=self.ticker,
                        timestamp = self.timestamp,
                        open = Decimal(80.90),
                        close = Decimal(9000.90),
                        high = Decimal(75.90),
                        low = Decimal(8800.09),
                        volume = np.uint64(880000))

        # Oberver Pattern 
        self.observer_bar_order_book = ChildObserver()
        self.valid_bardata_order_book.attach(self.observer_bar_order_book, EventType.MARKET_EVENT)

        # Test quotedata orderbook
        self.valid_quotedata_order_book = OrderBook(MarketDataType.QUOTE, self.mock_event_queue)
        self.valid_quote = QuoteData(ticker=self.ticker,
                            timestamp=self.timestamp,
                            ask=Decimal(34.989889),
                            ask_size=Decimal(2232.323232),
                            bid=Decimal(12.34456),
                            bid_size=Decimal(112.234345))
        
        # Oberver Pattern 
        self.observer_quote_order_book = ChildObserver()
        self.valid_quotedata_order_book.attach(self.observer_quote_order_book, EventType.MARKET_EVENT)

    # Basic Validation
    def test_data_type_valid(self):
        # Validate book data type stored
        self.assertEqual(self.valid_bardata_order_book.data_type, MarketDataType.BAR) 
        self.assertEqual(self.valid_quotedata_order_book.data_type, MarketDataType.QUOTE) 

    def test_insert_bar_valid(self):
        tickers = ['HEJ4', 'AAPL']
        
        # Test
        for ticker in tickers:
            self.valid_bardata_order_book._insert_bar(ticker = ticker, data=self.valid_bar)
        
        # Validation
        self.assertEqual(len(self.valid_bardata_order_book.book.keys()), len(tickers))
        self.assertEqual(self.valid_bardata_order_book.book['HEJ4'], self.valid_bar) 
        self.assertEqual(self.valid_bardata_order_book.book['AAPL'], self.valid_bar) 

    def test_insert_quote_valid(self):
        tickers = ['HEJ4', 'AAPL']
        expected_book = {tickers[0]: self.valid_quote, tickers[1]: self.valid_quote}

        # Test
        for ticker in tickers:
            self.valid_quotedata_order_book._insert_or_update_quote(ticker = ticker, quote_data=self.valid_quote)
        
        # Validation
        self.assertEqual(len(self.valid_quotedata_order_book.book.keys()), len(tickers)) 
        self.assertEqual(self.valid_quotedata_order_book.book['HEJ4'], self.valid_quote) 
        self.assertEqual(self.valid_quotedata_order_book.book['AAPL'], self.valid_quote) 
        self.assertEqual(self.valid_quotedata_order_book.book, expected_book) 
        
    def test_update_market_data_bar_valid(self):
        tickers = ['HEJ4', 'AAPL']
        timestamp = np.uint64(1651700000)
        data = {tickers[0]: self.valid_bar, tickers[1]: self.valid_bar}
        self.assertEqual(self.observer_bar_order_book.tester, None)
        
        # Test
        self.valid_bardata_order_book.update_market_data(data=data,timestamp=timestamp)

        # Validation
        self.mock_event_queue.put.assert_called_once_with(MarketEvent(timestamp=timestamp, data=data))
        self.assertEqual(len(self.valid_bardata_order_book.book.keys()), len(tickers))
        self.assertEqual(self.valid_bardata_order_book.book, data)
        self.assertEqual(self.observer_bar_order_book.tester, 4)

    def test_update_market_data_tick_valid(self):
        tickers = ['HEJ4', 'AAPL']
        timestamp = np.uint64(1651500000)
        data = {tickers[0]: self.valid_quote, tickers[1]: self.valid_quote}
        self.assertEqual(self.observer_quote_order_book.tester, None)
        
        # Test
        self.valid_quotedata_order_book.update_market_data(data=data,timestamp=timestamp)

        # Validation
        self.mock_event_queue.put.assert_called_once_with(MarketEvent(timestamp=timestamp, data=data))
        self.assertEqual(len(self.valid_quotedata_order_book.book.keys()), len(tickers))
        self.assertEqual(self.valid_quotedata_order_book.book, data)
        self.assertEqual(self.observer_quote_order_book.tester, 4)

    def test_current_price_bar_valid(self):
        tickers = ['HEJ4', 'AAPL']
        data = {tickers[0]: self.valid_bar, tickers[1]: self.valid_bar}
        self.valid_bardata_order_book.book = data
        
        # Test
        price = self.valid_bardata_order_book.current_price(ticker=tickers[0])

        # Validation
        self.assertEqual(price, data[tickers[0]].close)
        self.assertEqual(price, data[tickers[1]].close)
        self.assertEqual(type(price), float)

    def test_current_price_tick_valid(self):
        tickers = ['HEJ4', 'AAPL']
        data = {tickers[0]: self.valid_quote, tickers[1]: self.valid_quote}
        self.valid_quotedata_order_book.book = data

        # Test
        price = self.valid_quotedata_order_book.current_price(ticker=tickers[0])

        # Validation
        self.assertEqual(price, float((data[tickers[0]].ask + data[tickers[0]].bid )/2))
        self.assertEqual(price,  float((data[tickers[1]].ask + data[tickers[1]].bid )/2))
        self.assertEqual(type(price), float)
    
    def test_current_prices_bar_valid(self):
        tickers = ['HEJ4', 'AAPL']
        data = {tickers[0]: self.valid_bar, tickers[1]: self.valid_bar}
        self.valid_bardata_order_book.book = data
        
        # Test
        prices = self.valid_bardata_order_book.current_prices()
        
        # Validation
        self.assertEqual(prices[tickers[0]], data[tickers[0]].close)
        self.assertEqual(prices[tickers[1]], data[tickers[1]].close)
        self.assertEqual(type(prices), dict)

    def test_current_prices_tick_valid(self):
        tickers = ['HEJ4', 'AAPL']
        data = {tickers[0]: self.valid_quote, tickers[1]: self.valid_quote}
        self.valid_quotedata_order_book.book = data
        
        # Test
        prices = self.valid_quotedata_order_book.current_prices()

        # Validation
        self.assertEqual(prices[tickers[0]], (data[tickers[0]].ask + data[tickers[0]].bid )/2)
        self.assertEqual(prices[tickers[1]],  (data[tickers[1]].ask + data[tickers[1]].bid )/2)
        self.assertEqual(type(prices), dict)

    # Type Check
    def test_construction_data_type_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'data_type' field must be of type MarketDataType enum."):
            OrderBook(data_type='testing' , event_queue=self.mock_event_queue)

if __name__ == "__main__":
    unittest.main()