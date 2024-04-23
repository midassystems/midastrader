import  unittest
import numpy as np
from datetime import datetime
from ibapi.contract import Contract

from engine.events import OrderEvent
from shared.orders import Action, OrderType, BaseOrder, MarketOrder, LimitOrder, StopLoss

#TODO:  edge cases
class TestOrderEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(self.valid_action, 10)
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
    def test_type_constraint(self):
        self.invalid_timestamp = datetime(2024,1,1)
        with self.assertRaisesRegex(TypeError, "timestamp must be of type np.uint64."):
            OrderEvent(timestamp=self.invalid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id='1',
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id='2',
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
        with self.assertRaisesRegex(TypeError, "'action' must be of type Action enum."):
            OrderEvent(timestamp=self.valid_timestamp,
                    trade_id=self.valid_trade_id,
                    leg_id=self.valid_leg_id,
                    action=123,
                    order=self.valid_order,
                    contract=self.valid_contract)
            
        with self.assertRaisesRegex(TypeError, "'contract' must be of type Contract."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract="self.valid_contract")
            
        with self.assertRaisesRegex(TypeError, "'order' must be of type BaseOrder."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order="self.valid_order",
                           contract=self.valid_contract)

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            OrderEvent(timestamp=self.valid_timestamp,
                trade_id=-1,
                leg_id=self.valid_leg_id,
                action=self.valid_action,
                order=self.valid_order,
                contract=self.valid_contract)
            
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=0,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
              
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=-2,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
            
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=0,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)

if __name__ == "__main__":
    unittest.main()