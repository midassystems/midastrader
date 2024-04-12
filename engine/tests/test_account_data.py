import unittest
import random

from midas.account_data import Position, Trade

#TODO:  Edge case testing 

class TestPosition(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action =  random.choice(['BUY', 'SELL'])
        self.valid_avg_cost = 10.90
        self.valid_quantity = 100
        self.valid_multiplier = 10
        self.valid_initial_margin = 100.90
        self.valid_total_cost = 9000.90
        self.valid_market_value = 1000000.9
    
    # Basic Validation
    def test_construction(self):
        position = Position(action=self.valid_action,
                            avg_cost=self.valid_avg_cost,
                            quantity=self.valid_quantity,
                            multiplier=self.valid_multiplier,
                            initial_margin=self.valid_initial_margin,
                            total_cost=self.valid_total_cost,
                            market_value=self.valid_market_value)
    
        self.assertEqual(type(position), Position)
    
    def test_equality(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        self.assertTrue(new_position ==  base_position)

    def test_inequality_action(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="SELL", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_avg_cost(self):
        base_position = Position(action='BUY',
                    avg_cost=10,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=20,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_quantity(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=9,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=10,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_multiplier(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=60,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=90,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_initial_margin(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=9000,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=8657,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_total_cost(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=-9000,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=9000,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    # Type/Constraint Validation
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError, "action must be of type str"):
            Position(action=1234,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_avg_cost_type_validation(self):
        with self.assertRaisesRegex(TypeError, "avg_cost must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost="self.valid_avg_cost",
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"quantity must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity="self.valid_quantity",
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_multiplier_type_validation(self):
        with self.assertRaisesRegex(TypeError, "multiplier must be of type int"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier="self.valid_multiplier",
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_initial_margin_type_validation(self):
        with self.assertRaisesRegex(TypeError, "initial_margin must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin="self.valid_initial_margin",
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_total_cost_type_validation(self):
        with self.assertRaisesRegex(TypeError, "total_cost must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost="self.valid_total_cost,",
                        market_value=self.valid_market_value)
                
    def test_market_value_type_validation(self):
        with self.assertRaisesRegex(TypeError, "market_value must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value="self.valid_market_value)")

    def test_action_value_constraint(self):
        with self.assertRaisesRegex(ValueError,"action must be either 'BUY' or 'SELL'"):
            Position(action="Cover",
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        multiplier=self.valid_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_multiplier_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"multiplier must be greater than zero"):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                multiplier=-1,
                initial_margin=self.valid_initial_margin,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)
    
    def test_multiplier_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"multiplier must be greater than zero"):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                multiplier=0,
                initial_margin=self.valid_initial_margin,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)

    def test_initial_margin_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"initial_margin must be non-negative."):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                multiplier=self.valid_multiplier,
                initial_margin=-1.1,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)
            
    def test_equality_position_type_validation(self):
        base_position = Position(action=self.valid_action,
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    multiplier=self.valid_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        # Creating a random other object to compare to
        class RandomObject:
            def __init__(self):
                self.some_attribute = random.randint(1, 100)

        random_object = RandomObject()
        self.assertFalse(base_position == random_object, "A Position should not be equal to an instance of a different class")

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



