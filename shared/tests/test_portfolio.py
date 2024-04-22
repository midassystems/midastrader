import unittest
import random

from shared.portfolio import Position

#TODO:  Edge case testing 

class TestPosition(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action =  random.choice(['BUY', 'SELL'])
        self.valid_avg_cost = 10.90
        self.valid_quantity = 100
        self.quantity_multiplier = 10
        self.price_multiplier = 0.01
        self.valid_initial_margin = 100.90
        self.valid_total_cost = 9000.90
        self.valid_market_value = 1000000.9
    
    # Basic Validation
    def test_construction(self):
        position = Position(action=self.valid_action,
                            avg_cost=self.valid_avg_cost,
                            quantity=self.valid_quantity,
                            quantity_multiplier=self.quantity_multiplier,
                            price_multiplier=self.price_multiplier,
                            initial_margin=self.valid_initial_margin,
                            total_cost=self.valid_total_cost,
                            market_value=self.valid_market_value)
    
        self.assertEqual(type(position), Position)
    
    def test_equality(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        self.assertTrue(new_position ==  base_position)

    def test_inequality_action(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="SELL", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_avg_cost(self):
        base_position = Position(action='BUY',
                    avg_cost=10,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=20,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_quantity(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=9,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=10,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_multiplier(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=60,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=90,
                    initial_margin=self.valid_initial_margin,
                    price_multiplier=self.price_multiplier,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_initial_margin(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=9000,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=8657,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)

        self.assertFalse(new_position == base_position)

    def test_inequality_total_cost(self):
        base_position = Position(action='BUY',
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=-9000,
                    market_value=self.valid_market_value)
        
        new_position = Position(action="BUY", 
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
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
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_avg_cost_type_validation(self):
        with self.assertRaisesRegex(TypeError, "avg_cost must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost="self.valid_avg_cost",
                        quantity=self.valid_quantity,
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"quantity must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity="self.valid_quantity",
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)

    def test_multiplier_type_validation(self):
        with self.assertRaisesRegex(TypeError, "multiplier must be of type int"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        quantity_multiplier="self.quantity_multiplier",
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_initial_margin_type_validation(self):
        with self.assertRaisesRegex(TypeError, "initial_margin must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin="self.valid_initial_margin",
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_total_cost_type_validation(self):
        with self.assertRaisesRegex(TypeError, "total_cost must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost="self.valid_total_cost,",
                        market_value=self.valid_market_value)
                
    def test_market_value_type_validation(self):
        with self.assertRaisesRegex(TypeError, "market_value must be of type int or float"):
            Position(action=self.valid_action,
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value="self.valid_market_value)")

    def test_action_value_constraint(self):
        with self.assertRaisesRegex(ValueError,"action must be either 'BUY' or 'SELL'"):
            Position(action="Cover",
                        avg_cost=self.valid_avg_cost,
                        quantity=self.valid_quantity,
                        quantity_multiplier=self.quantity_multiplier,
                        price_multiplier=self.price_multiplier,
                        initial_margin=self.valid_initial_margin,
                        total_cost=self.valid_total_cost,
                        market_value=self.valid_market_value)
            
    def test_multiplier_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"multiplier must be greater than zero"):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                quantity_multiplier=-1,
                price_multiplier=self.price_multiplier,
                initial_margin=self.valid_initial_margin,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)
    
    def test_multiplier_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"multiplier must be greater than zero"):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                quantity_multiplier=0,
                price_multiplier=self.price_multiplier,
                initial_margin=self.valid_initial_margin,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)

    def test_initial_margin_negative_constraint(self):
        with self.assertRaisesRegex(ValueError,"initial_margin must be non-negative."):
            Position(action=self.valid_action,
                avg_cost=self.valid_avg_cost,
                quantity=self.valid_quantity,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                initial_margin=-1.1,
                total_cost=self.valid_total_cost,
                market_value=self.valid_market_value)
            
    def test_equality_position_type_validation(self):
        base_position = Position(action=self.valid_action,
                    avg_cost=self.valid_avg_cost,
                    quantity=self.valid_quantity,
                    quantity_multiplier=self.quantity_multiplier,
                    price_multiplier=self.price_multiplier,
                    initial_margin=self.valid_initial_margin,
                    total_cost=self.valid_total_cost,
                    market_value=self.valid_market_value)
        
        # Creating a random other object to compare to
        class RandomObject:
            def __init__(self):
                self.some_attribute = random.randint(1, 100)

        random_object = RandomObject()
        self.assertFalse(base_position == random_object, "A Position should not be equal to an instance of a different class")


if __name__ =="__main__":
    unittest.main()



