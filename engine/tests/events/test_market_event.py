import unittest
from datetime import datetime

from midas.events import QuoteData, BarData, MarketEvent

#TODO: Edge cases

class TestQuoteData(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = 1651500000
        self.valid_ask = 80.90
        self.valid_ask_size = 90000.9
        self.valid_bid = 75.90
        self.valid_bid_size = 9000.8
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        quote = QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
        # Validation
        self.assertEqual(quote.timestamp, self.valid_timestamp)
        self.assertEqual(quote.ask, self.valid_ask)
        self.assertEqual(quote.ask_size, self.valid_ask_size)
        self.assertEqual(quote.bid, self.valid_bid)
        self.assertEqual(quote.bid_size, self.valid_bid_size)

    # Type Validation
    def test_timestamp_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' should be in UNIX format of type float or int"):
            QuoteData(timestamp=datetime(2023,1,1),
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
            
    def test_ask_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'ask' must be of type float or int"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask="90.9",
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
    
    def test_ask_size_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'ask_size' must be of type float or int"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size="9000.9",
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
    
    def test_bid_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'bid' must be of type float or int"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid="6868",
                         bid_size = self.valid_bid_size)
            
    def test_bid_size_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'bid_size' must be of type float or int"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = "3745893.3")

    # Constraint Validation
    def test_ask_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'ask' must be greater than zero"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=-1,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
            
    def test_ask_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'ask' must be greater than zero"):
             QuoteData(timestamp=self.valid_timestamp,
                         ask=0,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
             
    def test_ask_size_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'ask_size' must be greater than zero"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=-10,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)
            
    def test_ask_size_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'ask_size' must be greater than zero"):
             QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=0.0,
                         bid=self.valid_bid,
                         bid_size = self.valid_bid_size)

    def test_bid_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'bid' must be greater than zero"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=-100,
                         bid_size = self.valid_bid_size)
            
    def test_bid_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'bid' must be greater than zero"):
             QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=0.0,
                         bid_size = self.valid_bid_size)
    
    def test_bid_size_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'bid_size' must be greater than zero"):
            QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = -100)
            
    def test_bid_size_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'bid_size' must be greater than zero"):
             QuoteData(timestamp=self.valid_timestamp,
                         ask=self.valid_ask,
                         ask_size=self.valid_ask_size,
                         bid=self.valid_bid,
                         bid_size = 0.0)

    # Edge Cases

class TestBarData(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = 1651500000
        self.valid_open = 80.90
        self.valid_close = 9000.90
        self.valid_high = 75.90
        self.valid_low = 8800.09
        self.valid_volume = 880000
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        bar = BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
        
        # Validation
        self.assertEqual(bar.timestamp, self.valid_timestamp)
        self.assertEqual(bar.open, self.valid_open)
        self.assertEqual(bar.close, self.valid_close)
        self.assertEqual(bar.high, self.valid_high)
        self.assertEqual(bar.low, self.valid_low)
        self.assertEqual(bar.volume, self.valid_volume)

    # Type Validation
    def test_timestamp_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' should be in UNIX format of type float or int"):
            BarData(timestamp=datetime(2024,1,1),
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_open_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'open' must be of type float or int"):
            BarData(timestamp=self.valid_timestamp,
                        open="self.valid_open",
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_high_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'high' must be of type float or int"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high="self.valid_high",
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_low_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'low' must be of type float or int"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = "self.valid_low",
                        volume=self.valid_volume)
            
    def test_close_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'close' must be of type float or int"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close="self.valid_close",
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_volume_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'volume' must be of type float or int"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume="self.valid_volume")
        
    # Constraint Validation
    def test_open_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'open' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=-100,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_open_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'open' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=0.0,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
    
    def test_high_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'high' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=-100,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_high_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'high' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=0.0,
                        low = self.valid_low,
                        volume=self.valid_volume)
    
    def test_low_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'low' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = -90.4,
                        volume=self.valid_volume)
            
    def test_low_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'low' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = 0.0,
                        volume=self.valid_volume)
    
    def test_close_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'close' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=-90,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
            
    def test_close_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'close' must be greater than zero"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=0.0,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=self.valid_volume)
    
    def test_volume_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'volume' must be non-negative"):
            BarData(timestamp=self.valid_timestamp,
                        open=self.valid_open,
                        close=self.valid_close,
                        high=self.valid_high,
                        low = self.valid_low,
                        volume=-3737)
            
    # Edge Cases

class TestMarketEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = 1651500000
        self.valid_bar = BarData(timestamp = 1651500000,
                        open = 80.90,
                        close = 9000.90,
                        high = 75.90,
                        low = 8800.09,
                        volume = 880000)
        
        self.valid_data = {'AAPL': self.valid_bar}

    # Basic Validation
    def test_valid_construction(self):

        event = MarketEvent(data=self.valid_data, timestamp=self.valid_timestamp)

        self.assertEqual(event.data['AAPL'].timestamp, self.valid_bar.timestamp)
        self.assertEqual(event.data['AAPL'].open, self.valid_bar.open)
        self.assertEqual(event.data['AAPL'].high, self.valid_bar.high)
        self.assertEqual(event.data['AAPL'].low, self.valid_bar.low)
        self.assertEqual(event.data['AAPL'].close, self.valid_bar.close)
        self.assertEqual(event.data['AAPL'].volume, self.valid_bar.volume)
        self.assertEqual(event.timestamp, self.valid_timestamp)

    def test_valid_construction_w_intraday_timestamp(self):
        isoformat_date= 1651500000.000
        self.valid_data['AAPL'].timestamp = isoformat_date
        
        event = MarketEvent(data=self.valid_data, timestamp=isoformat_date)

        self.assertEqual(event.data['AAPL'].timestamp, self.valid_bar.timestamp)
        self.assertEqual(event.data['AAPL'].open, self.valid_bar.open)
        self.assertEqual(event.data['AAPL'].high, self.valid_bar.high)
        self.assertEqual(event.data['AAPL'].low, self.valid_bar.low)
        self.assertEqual(event.data['AAPL'].close, self.valid_bar.close)
        self.assertEqual(event.data['AAPL'].volume, self.valid_bar.volume)
        self.assertEqual(event.timestamp, isoformat_date)

    # Type Validation
    def test_timestamp_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int"):
            MarketEvent(data=self.valid_data, timestamp=datetime(2024,1,1))
    
    def test_data_dict_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'data' must be of type dict" ):
            MarketEvent(data=[1,2,3], timestamp=self.valid_timestamp)
    
    def test_data_key_type_validation(self):
        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type and all values 'data' must be instances of MarketData" ):
            MarketEvent(data={1:1,2:1,3:1}, timestamp=self.valid_timestamp)
            
    def test_data_marketdata_type_validation(self):
        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type and all values 'data' must be instances of MarketData" ):
            MarketEvent(data={"AAPL":1,"'TSLA":1}, timestamp=self.valid_timestamp)

    def test_none_values_handling(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int"):
            MarketEvent(data=self.valid_data, timestamp=None)
    
        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type and all values 'data' must be instances of MarketData"):
            MarketEvent(data={'AAPL': None}, timestamp=self.valid_timestamp)

    # Constraint Validation
    def test_invalid_timestamp_format(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int,"):
            MarketEvent(data=self.valid_data, timestamp="14-10-2020")

    def test_empty_data_validation(self):
        with self.assertRaisesRegex(ValueError, "'data' dictionary cannot be empty"):
            MarketEvent(data={}, timestamp=self.valid_timestamp)

if __name__ == "__main__":
    unittest.main()