import random
import unittest
import numpy as np
from datetime import datetime
from ibapi.contract import Contract
from midas.shared.trade import Trade
from midas.shared.orders import Action
from midas.engine.events import ExecutionEvent

class TestExecutionEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test Data
        self.timetamp = np.uint64(1651500000)
        self.trade_details = Trade(
            timestamp = np.uint64(1651500000),
            trade_id = 1,
            leg_id = 2,
            ticker = 'HEJ4',
            quantity = -10,
            avg_price = 9.9,
            trade_value=103829083,
            trade_cost = 9000.99,
            action = Action.LONG.value,
            fees = 9.78
        )
        self.action = random.choice([Action.LONG,Action.COVER,Action.SELL,Action.SHORT])
        self.contract = Contract()
    
    # Basic Validation
    def test_valid_construction(self):
        # Test
        exec = ExecutionEvent(timestamp=self.timetamp,
                               trade_details=self.trade_details,
                               action=self.action,
                               contract=self.contract)
        # Validation
        self.assertEqual(exec.timestamp, self.timetamp)
        self.assertEqual(exec.action, self.action)
        self.assertEqual(exec.contract, self.contract)
        self.assertEqual(exec.trade_details, self.trade_details)
        self.assertEqual(type(exec.action), Action)
        self.assertEqual(type(exec.contract), Contract)

    # Type Check
    def test_type_constraint(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' field must be of type np.uint64."):
            ExecutionEvent(timestamp=datetime(2024,1,1),
                               trade_details=self.trade_details,
                               action=self.action,
                               contract=self.contract)
            
        with self.assertRaisesRegex(TypeError, "'action' field must be of type Action enum."): 
            ExecutionEvent(timestamp=self.timetamp,
                               trade_details=self.trade_details,
                               action="self.action",
                               contract=self.contract)
            
        with self.assertRaisesRegex(TypeError, "'trade_details' field must be of type Trade instance."): 
            ExecutionEvent(timestamp=self.timetamp,
                               trade_details="self.trade_details,",
                               action=self.action,
                               contract=self.contract)
            
        with self.assertRaisesRegex(TypeError, "'contract' field must be of type Contract instance."): 
            ExecutionEvent(timestamp=self.timetamp,
                               trade_details=self.trade_details,
                               action=self.action,
                               contract="self.contract")
         

if __name__=="__main__":
    unittest.main()
