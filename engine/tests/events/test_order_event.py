import  unittest
from datetime import datetime
from ibapi.order import Order
from ibapi.contract import Contract

from midas.events import Action, OrderType, BaseOrder, MarketOrder, LimitOrder, StopLoss, OrderEvent

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

        base_order = BaseOrder(action=action,
                                quantity=quantity,
                                orderType=self.valid_order_type)
        
        self.assertEqual(base_order.order.totalQuantity, abs(quantity)) # confirm Order quantity positive
        self.assertEqual(base_order.quantity, quantity) # confrim quantity property returned based on direction (positive)

    def test_negative_quantity_property(self):
        quantity = -110
        action = Action.SHORT

        base_order = BaseOrder(action=action,
                                quantity=quantity,
                                orderType=self.valid_order_type)
        
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

class TestOrderEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = 1651500000
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(self.valid_action, 10 )
        self.valid_contract = Contract()

    # Basic Validation                
    def test_basic_validation(self):
        event = OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
        
        self.assertEqual(event.timestamp, self.valid_timestamp)
        self.assertEqual(event.order, self.valid_order)
        self.assertEqual(event.contract, self.valid_contract)
        self.assertEqual(event.action, self.valid_action)
        self.assertEqual(event.trade_id, self.valid_trade_id)
        self.assertEqual(event.leg_id, self.valid_leg_id)

    # Type Checks
    def test_timestamp_type_valdiation(self):
        self.invalid_timestamp = datetime(2024,1,1)
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int"):
            OrderEvent(timestamp=self.invalid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
    def test_trade_id_type_valdiation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id='1',
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
    def test_leg_id_type_valdiation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id='2',
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
    def test_action_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'action' must be of type Action enum."):
            OrderEvent(timestamp=self.valid_timestamp,
                    trade_id=self.valid_trade_id,
                    leg_id=self.valid_leg_id,
                    action=123,
                    order=self.valid_order,
                    contract=self.valid_contract)
            
    def test_contract_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'contract' must be of type Contract."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract="self.valid_contract")
            
    def test_order_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'order' must be of type BaseOrder."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order="self.valid_order",
                           contract=self.valid_contract)

    # Constraint Check
    def test_timestamp_format_valdiation(self):
        self.invalid_timestamp = "01-01-2024"
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int,"):
            OrderEvent(timestamp=self.invalid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
    def test_timestamp_none_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int"):
            OrderEvent(timestamp=None,
                trade_id=self.valid_trade_id,
                leg_id=self.valid_leg_id,
                action=self.valid_action,
                order=self.valid_order,
                contract=self.valid_contract)

    def test_trade_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            OrderEvent(timestamp=self.valid_timestamp,
                trade_id=-1,
                leg_id=self.valid_leg_id,
                action=self.valid_action,
                order=self.valid_order,
                contract=self.valid_contract)
            
    def test_trade_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=0,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
              
    def test_leg_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=-2,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
    def test_leg_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=0,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)

if __name__ == "__main__":
    unittest.main()