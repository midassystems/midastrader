import random
import unittest
import numpy as np
from midas.shared.trade import Trade

class TestTrade(unittest.TestCase):
    def setUp(self) -> None:
        # Mock trade data
        self.valid_trade_id = 1
        self.valid_leg_id = 2
        self.valid_timetamp = np.uint64(16555000)
        self.valid_ticker = 'HEJ4'
        self.valid_quantity = 10
        self.valid_avg_price= 85.98
        self.valid_trade_value = 900.90
        self.valid_action = random.choice(['BUY', 'SELL'])
        self.valid_fees = 9.87

        # Creaet trade object
        self.trade_obj = Trade(trade_id=self.valid_trade_id,
                leg_id=self.valid_leg_id,
                timestamp=self.valid_timetamp,
                ticker=self.valid_ticker,
                quantity=self.valid_quantity,
                avg_price=self.valid_avg_price,
                trade_value=self.valid_trade_value,
                action=self.valid_action,
                fees=self.valid_fees)
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        trade = Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value, 
                      action=self.valid_action,
                      fees=self.valid_fees)
        # Validate
        self.assertEqual(trade.trade_id, self.valid_trade_id)
        self.assertEqual(trade.leg_id, self.valid_leg_id)
        self.assertEqual(trade.timestamp, self.valid_timetamp)
        self.assertEqual(trade.ticker, self.valid_ticker)
        self.assertEqual(trade.quantity, self.valid_quantity)
        self.assertEqual(trade.avg_price, self.valid_avg_price)
        self.assertEqual(trade.trade_value, self.valid_trade_value)
        self.assertEqual(trade.action, self.valid_action)
        self.assertEqual(trade.fees, self.valid_fees)

    # Type Validation
    def test_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'trade_id' field must be of type int."):
            Trade(trade_id="1",
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError, "'leg_id' field must be of type int."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id="2",
                      timestamp=self.valid_timetamp,
                     ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError,"'timestamp' field must be of type np.uint64."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp="2022-08-08",
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError,"'ticker' field must be of type str."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=1,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError,"'quantity' field must be of type float or int."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity="1234",
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError,"'avg_price' field must be of type float or int."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price="90.9",
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)
               
        with self.assertRaisesRegex(TypeError,"'trade_value' field must be of type float or int."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value="12345",
                      action=self.valid_action,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError, "'action' field must be of type str."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=12234,
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(TypeError, "'fees' field must be of type float or int."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees="90.99")
            
    # Value validation
    def test_value_constraint(self):
        with self.assertRaises(ValueError):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=self.valid_avg_price,
                      trade_value=self.valid_trade_value,
                      action='long',
                      fees=self.valid_fees)
            
        with self.assertRaisesRegex(ValueError, "'avg_price' field must be greater than zero."):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      avg_price=0.0,
                      trade_value=self.valid_trade_value,
                      action=self.valid_action,
                      fees=self.valid_fees)

if __name__ =="__main__":
    unittest.main()



