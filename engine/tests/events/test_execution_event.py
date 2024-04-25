import random
import unittest
import numpy as np
from ibapi.order import Order
from datetime import datetime
from ibapi.contract import Contract

from engine.events import ExecutionEvent

from shared.orders import Action
from shared.trade import ExecutionDetails

# TOOO : edge cases
class TestExecutionEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timetamp = np.uint64(1651500000)
        self.valid_trade_details =ExecutionDetails(
                                                    timestamp = 1651500000 ,
                                                    trade_id = 1,
                                                    leg_id = 2,
                                                    symbol = 'HEJ4',
                                                    quantity = -10,
                                                    price = -9.9,
                                                    cost = 9000.99,
                                                    action = Action.LONG.value,
                                                    fees = 9.78
                                                )
        self.valid_action = random.choice([Action.LONG,Action.COVER,Action.SELL,Action.SHORT])
        self.valid_contract = Contract()
        self.valid_order = Order()
    
    # Basic Validation
    def test_valid_construction(self):
        # test
        exec = ExecutionEvent(timestamp=self.valid_timetamp,
                               trade_details=self.valid_trade_details,
                               action=self.valid_action,
                               contract=self.valid_contract)
        # validation
        self.assertEqual(exec.timestamp, self.valid_timetamp)
        self.assertEqual(exec.action, self.valid_action)
        self.assertEqual(exec.contract, self.valid_contract)
        self.assertEqual(exec.trade_details, self.valid_trade_details)
        self.assertEqual(type(exec.action), Action)
        self.assertEqual(type(exec.contract), Contract)

    # Type Check
    def test_type_constraint(self):
        with self.assertRaisesRegex(TypeError,"timestamp must be of type np.uint64."):
            ExecutionEvent(timestamp=datetime(2024,1,1),
                               trade_details=self.valid_trade_details,
                               action=self.valid_action,
                               contract=self.valid_contract)
            
        with self.assertRaisesRegex(TypeError, "'action' must be of type Action enum."): 
            ExecutionEvent(timestamp=self.valid_timetamp,
                               trade_details=self.valid_trade_details,
                               action="self.valid_action",
                               contract=self.valid_contract)
            
        with self.assertRaisesRegex(TypeError,"'trade_details' must be of type ExecutionDetails dict."): 
            ExecutionEvent(timestamp=self.valid_timetamp,
                               trade_details="self.valid_trade_details,",
                               action=self.valid_action,
                               contract=self.valid_contract)
            
        with self.assertRaisesRegex(TypeError,"'contract' must be of type Contract instance."): 
            ExecutionEvent(timestamp=self.valid_timetamp,
                               trade_details=self.valid_trade_details,
                               action=self.valid_action,
                               contract="self.valid_contract")
         
    

if __name__=="__main__":
    unittest.main()