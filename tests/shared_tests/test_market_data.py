import unittest
import numpy as np
import pandas as pd
from decimal import Decimal

from midas.shared.market_data import QuoteData, BarData, dataframe_to_bardata, round_decimal

#TODO: Edge cases / round decimal
      
class TestBarData(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="AAPL"   
        self.timestamp=np.uint64(1707221160000000000)
        self.open=Decimal(100.990808)
        self.high=Decimal(1111.9998)
        self.low=Decimal(99.990898)
        self.close=Decimal(105.9089787)
        self.volume=np.uint64(100000909)
    
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
            "open": str(round_decimal(self.open)),
            "close": str(round_decimal(self.close)),
            "high": str(round_decimal(self.high)),
            "low": str(round_decimal(self.low)),
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
            
        with self.assertRaisesRegex(TypeError,"timestamp must be of type np.uint64." ):
            BarData(ticker=self.ticker,
                      timestamp="123456",
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
            
        with self.assertRaisesRegex(TypeError,"volume must be of type np.uint64."):
            BarData(ticker=self.ticker,
                      timestamp=self.timestamp,
                      open=self.open,
                      high=self.high,
                      low=self.low,
                      close=self.close,
                      volume="123456")

class TestDataframeToBardata(unittest.TestCase):
    def setUp(self) -> None:
        self.data = {
            'rtype': [33, 33, 33, 33, 33],
            'publisher_id': [1, 1, 1, 1, 1],
            'instrument_id': [243778, 243778, 243778, 243778, 243778],
            'open': [443.50, 443.50, 443.50, 443.50, 443.50],
            'high': [443.75, 443.50, 443.50, 443.75, 443.50],
            'low': [443.50, 443.50, 443.50, 443.50, 443.50],
            'close': [443.75, 443.50, 443.50, 443.75, 443.50],
            'volume': [20, 11, 100, 27, 10],
            'symbol': ['ZC.n.0', 'ZC.n.0', 'ZC.n.0', 'ZC.n.0', 'ZC.n.0']
        }

        # Create the DataFrame
        self.df = pd.DataFrame(self.data)

        # Set the index to be a datetime type
        self.df.index = pd.to_datetime([
            '2024-02-06 12:00:00+00:00',
            '2024-02-06 12:01:00+00:00',
            '2024-02-06 12:02:00+00:00',
            '2024-02-06 12:03:00+00:00',
            '2024-02-06 12:06:00+00:00'
        ]).astype(np.int64).astype(np.uint64)


        # If you want the index to have a name 'ts_event'
        self.df.index.name = 'ts_event'

    def test_valid(self):
        # test
        data_list=dataframe_to_bardata(self.df)

        # validate
        self.assertEqual(len(data_list), 5)

class TestQuoteData(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker="AAPL"   
        self.timestamp=np.uint64(1707221160000000000)
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
            
        with self.assertRaisesRegex(TypeError,"timestamp must be of type np.uint64."):
            QuoteData(ticker=self.ticker,
                      timestamp="123456",
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
          

if __name__ == "__main__":
    unittest.main()