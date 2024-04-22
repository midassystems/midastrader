import random
import unittest

from shared.trade import Trade

class TestTrade(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_trade_id = 1
        self.valid_leg_id = 2
        self.valid_timetamp = 16555000
        self.valid_ticker = 'HEJ4'
        self.valid_quantity = 10
        self.valid_price= 85.98
        self.valid_cost = 900.90
        self.valid_action = random.choice(['BUY', 'SELL'])
        self.valid_fees = 9.87
    
    # Basic Validation
    def test_valid_construction(self):
        trade = Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
        
        self.assertEqual(trade.trade_id, self.valid_trade_id)
        self.assertEqual(trade.leg_id, self.valid_leg_id)
        self.assertEqual(trade.timestamp, self.valid_timetamp)
        self.assertEqual(trade.ticker, self.valid_ticker)
        self.assertEqual(trade.quantity, self.valid_quantity)
        self.assertEqual(trade.price, self.valid_price)
        self.assertEqual(trade.cost, self.valid_cost)
        self.assertEqual(trade.action, self.valid_action)
        self.assertEqual(trade.fees, self.valid_fees)

    # Type Validation
    def test_trade_id_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'trade_id' must be of type int"):
            Trade(trade_id="1",
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_leg_id_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'leg_id' must be of type int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id="2",
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_timestamp_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' should be in UNIX format of type float or int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp="2022-08-08",
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'ticker' must be of type str"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=1234,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'quantity' must be of type float or int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity="1234",
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_price_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'price' must be of type float or int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price="90.9",
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_cost_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'cost' must be of type float or int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost="90.90",
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'action' must be of type str"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=12234,
                      fees=self.valid_fees)
            
    def test_fees_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'fees' must be of type float or int"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees="90.99")
            
    # Constraint validation
    def test_action_constraint(self):
        with self.assertRaisesRegex(ValueError,"'action' must be either 'BUY', 'SELL', 'LONG', 'SHORT', 'COVER'"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=self.valid_price,
                      cost=self.valid_cost,
                      action='long',
                      fees=self.valid_fees)
            
    def test_price_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"'price' must be greater than zero"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=-1.0,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)
            
    def test_price_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'price' must be greater than zero"):
            Trade(trade_id=self.valid_trade_id,
                      leg_id=self.valid_leg_id,
                      timestamp=self.valid_timetamp,
                      ticker=self.valid_ticker,
                      quantity=self.valid_quantity,
                      price=0.0,
                      cost=self.valid_cost,
                      action=self.valid_action,
                      fees=self.valid_fees)

if __name__ =="__main__":
    unittest.main()



