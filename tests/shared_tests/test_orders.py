import unittest
from ibapi.order import Order

from midas.shared.orders import Action, OrderType, BaseOrder, MarketOrder, LimitOrder, StopLoss

#TODO:  edge cases

class TestAction(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_long = Action.LONG
        self.valid_short = Action.SHORT
        self.valid_sell = Action.SELL
        self.valid_cover = Action.COVER

    # Basic Validation
    def test_valid_long_to_broker_standard(self):
        # Test
        result = self.valid_long.to_broker_standard()
        
        # Validation
        self.assertEqual("BUY", result) # LONG should be a 'BUY'

    def test_valid_cover_to_broker_standard(self):
        # Test
        result = self.valid_cover.to_broker_standard()
        
        # Validation
        self.assertEqual("BUY", result) # COVER should be a 'BUY'

    def test_valid_sell_to_broker_standard(self):
        # Test
        result = self.valid_sell.to_broker_standard()
        
        # Validation
        self.assertEqual("SELL", result) # SELL should be a 'SELL'

    def test_valid_short_to_broker_standard(self):
        # Test
        result = self.valid_short.to_broker_standard()

        # Validation
        self.assertEqual("SELL", result)  # SHORT should be a 'SELL'

    # Type Check
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            Action('INVALID_ACTION') 
        
class TestBaseOrder(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action = Action.LONG
        self.valid_quantity = 20
        self.valid_order_type = OrderType.MARKET
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        base_order = BaseOrder(action=self.valid_action,
                               quantity=self.valid_quantity,
                               orderType=self.valid_order_type)

        # Validation
        self.assertEqual(type(base_order.order), Order) # creation of ibapi Order object
        self.assertEqual(base_order.order.action, self.valid_action.to_broker_standard()) # conversion of Action Enum to ibapi standard
        self.assertEqual(base_order.order.totalQuantity, abs(self.valid_quantity)) # quantity = abs of given quanity per ib standard
        self.assertEqual(base_order.order.orderType, self.valid_order_type.value) # Ordertype enum correctly applied

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG

        # test
        base_order = BaseOrder(action=action,
                                quantity=quantity,
                                orderType=self.valid_order_type)
        # validate
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction (positive)

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT

        # test 
        base_order = BaseOrder(action=action,
                                quantity=quantity,
                                orderType=self.valid_order_type)
        # validate
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction (negative)

    # Type Check
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            BaseOrder(action='self.valid_action,',
                        quantity=self.valid_quantity,
                        orderType=self.valid_order_type)
            
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'quantity' must be type float or int." ):
            BaseOrder(action=self.valid_action,
                        quantity="self.valid_quantity",
                        orderType=self.valid_order_type)
    
    def test_orderType_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'orderType' must be type OrderType enum." ):
            BaseOrder(action=self.valid_action,
                        quantity=self.valid_quantity,
                        orderType=123) 

    # Constraint Check
    def test_quantity_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'quantity' must not be zero."):
            BaseOrder(action=self.valid_action,
                        quantity=0.0,
                        orderType=self.valid_order_type)

    def test_action_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            BaseOrder(action=None,
                        quantity=self.valid_quantity,
                        orderType=self.valid_order_type)
            
    def test_quantity_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'quantity' must be type float or int."):
            BaseOrder(action=self.valid_action,
                        quantity=None,
                        orderType=self.valid_order_type)

    def test_order_type_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'orderType' must be type OrderType enum."):
            BaseOrder(action=self.valid_action,
                        quantity=self.valid_quantity,
                        orderType=None)

class TestMarketOrder(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action = Action.LONG
        self.valid_quantity = 20
        self.valid_order_type = OrderType.MARKET
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        base_order = MarketOrder(action=self.valid_action,
                               quantity=self.valid_quantity)

        # Validation
        self.assertEqual(type(base_order.order), Order) # creation of ibapi Order object
        self.assertEqual(base_order.order.action, self.valid_action.to_broker_standard()) # conversion of Action Enum to ibapi standard
        self.assertEqual(base_order.order.totalQuantity, abs(self.valid_quantity)) # quantity = abs of given quanity per ib standard
        self.assertEqual(base_order.order.orderType, self.valid_order_type.value) # Ordertype enum correctly applied

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG
        # Test
        base_order = MarketOrder(action=action,
                                quantity=quantity)
        
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT
        # Test
        base_order = MarketOrder(action=action,
                                quantity=quantity)
        
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    # Type Check
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            MarketOrder(action='self.valid_action,',
                        quantity=self.valid_quantity)
            
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'quantity' must be type float or int." ):
            MarketOrder(action=self.valid_action,
                        quantity="self.valid_quantity")
    
    # Constraint Check
    def test_quantity_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'quantity' must not be zero."):
            MarketOrder(action=self.valid_action,
                        quantity=0.0)

    def test_action_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            MarketOrder(action=None,
                        quantity=self.valid_quantity)
            
    def test_quantity_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'quantity' must be type float or int."):
            MarketOrder(action=self.valid_action,
                        quantity=None)

class TestLimitOrder(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action = Action.LONG
        self.valid_quantity = 20
        self.valid_limit_price = 100.9
        self.valid_order_type = OrderType.LIMIT
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        base_order = LimitOrder(action=self.valid_action,
                               quantity=self.valid_quantity,
                               limit_price=self.valid_limit_price)

        # Validation
        self.assertEqual(type(base_order.order), Order) # creation of ibapi Order object
        self.assertEqual(base_order.order.action, self.valid_action.to_broker_standard()) # conversion of Action Enum to ibapi standard
        self.assertEqual(base_order.order.totalQuantity, abs(self.valid_quantity)) # quantity = abs of given quanity per ib standard
        self.assertEqual(base_order.order.orderType, self.valid_order_type.value) # Ordertype enum correctly applied
        self.assertEqual(base_order.order.lmtPrice, self.valid_limit_price) # check limit price set

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG
        # Test
        base_order = LimitOrder(action=action,
                                quantity=quantity,
                                limit_price=self.valid_limit_price)
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT
        # Test
        base_order = LimitOrder(action=action,
                                quantity=quantity,
                                limit_price=self.valid_limit_price)
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    # Type Check
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            LimitOrder(action='self.valid_action,',
                        quantity=self.valid_quantity,
                        limit_price=self.valid_limit_price)
            
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'quantity' must be type float or int." ):
            LimitOrder(action=self.valid_action,
                        quantity="self.valid_quantity",
                        limit_price=self.valid_limit_price)
    
    def test_limit_price_validation(self):
        with self.assertRaisesRegex(TypeError,"'limit_price' must be of type float or int."):
            LimitOrder(action=self.valid_action,
                        quantity=self.valid_quantity,
                        limit_price="self.valid_limit_price")
    
    # Constraint Check
    def test_quantity_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'quantity' must not be zero."):
            LimitOrder(action=self.valid_action,
                        quantity=0,
                        limit_price=self.valid_limit_price)

    def test_action_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            LimitOrder(action=None,
                        quantity=self.valid_quantity,
                        limit_price=self.valid_limit_price)
            
    def test_quantity_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'quantity' must be type float or int."):
            LimitOrder(action=self.valid_action,
                        quantity=None, 
                        limit_price=self.valid_limit_price)
                        
    def test_limit_price_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'limit_price' must be greater than zero."):
            LimitOrder(action=self.valid_action,
                        quantity=self.valid_quantity, 
                        limit_price=0.0)

class TestStopLoss(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_action = Action.LONG
        self.valid_quantity = 20
        self.valid_aux_price = 100.9
        self.valid_order_type = OrderType.STOPLOSS
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        base_order = StopLoss(action=self.valid_action,
                               quantity=self.valid_quantity,
                               aux_price=self.valid_aux_price)
        # Validation
        self.assertEqual(type(base_order.order), Order) # creation of ibapi Order object
        self.assertEqual(base_order.order.action, self.valid_action.to_broker_standard()) # conversion of Action Enum to ibapi standard
        self.assertEqual(base_order.order.totalQuantity, abs(self.valid_quantity)) # quantity = abs of given quanity per ib standard
        self.assertEqual(base_order.order.orderType, self.valid_order_type.value) # Ordertype enum correctly applied
        self.assertEqual(base_order.order.auxPrice, self.valid_aux_price) # check stop price set

    def test_positiive_quantity_property(self):
        quantity = 10
        action = Action.LONG
        # Test
        base_order = StopLoss(action=action,
                               quantity=quantity,
                               aux_price=self.valid_aux_price)
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT
        # Test
        base_order = StopLoss(action=action,
                               quantity=quantity,
                               aux_price=self.valid_aux_price)
        # Validation
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction

    # Type Check
    def test_action_type_validation(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            StopLoss(action='self.valid_action,',
                        quantity=self.valid_quantity,
                        aux_price=self.valid_aux_price)
            
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'quantity' must be type float or int." ):
            StopLoss(action=self.valid_action,
                        quantity="self.valid_quantity",
                        aux_price=self.valid_aux_price)
    
    def test_aux_price_validation(self):
        with self.assertRaisesRegex(TypeError,"'aux_price' must be of type float or int."):
            StopLoss(action=self.valid_action,
                        quantity=self.valid_quantity,
                        aux_price="self.valid_aux_price")
    
    # Constraint Check
    def test_quantity_zero_constraint(self):
        with self.assertRaisesRegex(ValueError,"'quantity' must not be zero."):
            StopLoss(action=self.valid_action,
                        quantity=0,
                        aux_price=self.valid_aux_price)

    def test_action_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'action' must be type Action enum."):
            StopLoss(action=None,
                        quantity=self.valid_quantity,
                        aux_price=self.valid_aux_price)
            
    def test_quantity_missing_constraint(self):
        with self.assertRaisesRegex(TypeError, "'quantity' must be type float or int."):
            StopLoss(action=self.valid_action,
                        quantity=None, 
                        aux_price=self.valid_aux_price)
                        
    def test_aux_price_zero_constraint(self):
        with self.assertRaisesRegex(ValueError, "'aux_price' must be greater than zero."):
            StopLoss(action=self.valid_action,
                        quantity=self.valid_quantity, 
                        aux_price=0.0)

if __name__ == "__main__":
    unittest.main()