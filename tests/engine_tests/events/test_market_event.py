import unittest
import numpy as np
from decimal import Decimal
from datetime import datetime

from midas.engine.events import MarketEvent
from midas.shared.market_data import QuoteData, BarData

#TODO: Edge cases

class TestMarketEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.timestamp = np.uint64(1707221160000000000)
        self.ticker="AAPL"
        self.valid_bar = BarData(ticker=self.ticker,
                        timestamp = self.timestamp,
                        open = Decimal(80.90),
                        close = Decimal(9000.90),
                        high = Decimal(75.90),
                        low = Decimal(8800.09),
                        volume = np.uint64(880000))
        
        self.valid_data = {'AAPL': self.valid_bar}

    # Basic Validation
    def test_valid_construction(self):
        # test
        event = MarketEvent(data=self.valid_data, timestamp=self.timestamp)

        # validate
        self.assertEqual(event.data['AAPL'].timestamp, self.valid_bar.timestamp)
        self.assertEqual(event.data['AAPL'].open, self.valid_bar.open)
        self.assertEqual(event.data['AAPL'].high, self.valid_bar.high)
        self.assertEqual(event.data['AAPL'].low, self.valid_bar.low)
        self.assertEqual(event.data['AAPL'].close, self.valid_bar.close)
        self.assertEqual(event.data['AAPL'].volume, self.valid_bar.volume)
        self.assertEqual(event.timestamp, self.timestamp)

    # Type Validation
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError, "timestamp must be of type np.uint64."):
            MarketEvent(data=self.valid_data, timestamp=datetime(2024,1,1))
    
        with self.assertRaisesRegex(TypeError, "'data' must be of type dict" ):
            MarketEvent(data=[1,2,3], timestamp=self.timestamp)

        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type str and all values 'data' must be instances of MarketData" ):
            MarketEvent(data={1:1,2:1,3:1}, timestamp=self.timestamp)
            
        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type str and all values 'data' must be instances of MarketData" ):
            MarketEvent(data={"AAPL":1,"'TSLA":1}, timestamp=self.timestamp)

        with self.assertRaisesRegex(TypeError,"timestamp must be of type np.uint64."):
            MarketEvent(data=self.valid_data, timestamp=None)
    
        with self.assertRaisesRegex(TypeError, "all keys in 'data' must be of type str and all values 'data' must be instances of MarketData"):
            MarketEvent(data={'AAPL': None}, timestamp=self.timestamp)

        with self.assertRaisesRegex(TypeError, "timestamp must be of type np.uint64."):
            MarketEvent(data=self.valid_data, timestamp="14-10-2020")
            
    # Constraint Validation
    def test_value_constraints(self):
        with self.assertRaisesRegex(ValueError, "'data' dictionary cannot be empty"):
            MarketEvent(data={}, timestamp=self.timestamp)

if __name__ == "__main__":
    unittest.main()