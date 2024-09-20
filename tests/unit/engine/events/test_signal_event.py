import unittest
import numpy as np
from datetime import datetime
from midas.engine.events import SignalEvent
from midas.shared.orders import OrderType, Action
from midas.shared.signal import TradeInstruction

class TestSignalEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = np.uint64(1651500000)
        self.trade_capital = 1000090
        self.trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=10)
        self.trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5,
                                                quantity=10)
        self.trade_instructions = [self.trade1,self.trade2]
                        
    # Basic Validation
    def test_construction(self):
        # Test
        signal = SignalEvent(self.timestamp, self.trade_instructions)

        # Validate timestamp
        self.assertEqual(signal.timestamp,self.timestamp)
        
        # Validate first set of trade instructions
        self.assertEqual(signal.trade_instructions[0].ticker, self.trade1.ticker)
        self.assertEqual(signal.trade_instructions[0].order_type, self.trade1.order_type)
        self.assertEqual(signal.trade_instructions[0].action, self.trade1.action)
        self.assertEqual(signal.trade_instructions[0].trade_id, self.trade1.trade_id)
        self.assertEqual(signal.trade_instructions[0].leg_id, self.trade1.leg_id)
        self.assertEqual(signal.trade_instructions[0].weight, self.trade1.weight)
        
        # Validate second set of trade instructions
        self.assertEqual(signal.trade_instructions[1].ticker, self.trade2.ticker)
        self.assertEqual(signal.trade_instructions[1].order_type, self.trade2.order_type)
        self.assertEqual(signal.trade_instructions[1].action, self.trade2.action)
        self.assertEqual(signal.trade_instructions[1].trade_id, self.trade2.trade_id)
        self.assertEqual(signal.trade_instructions[1].leg_id, self.trade2.leg_id)
        self.assertEqual(signal.trade_instructions[1].weight, self.trade2.weight)

    def test_to_dict(self):
        signal = SignalEvent(timestamp=self.timestamp, trade_instructions=self.trade_instructions)
        
        # Test
        signal_dict = signal.to_dict()

        # Validation
        self.assertEqual(signal_dict['timestamp'], self.timestamp) 
        self.assertEqual(len(signal_dict['trade_instructions']), len(self.trade_instructions)) # checkall trade instructions include in serialization

    # Type Check
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' field must be of type np.uint64."):
            SignalEvent(timestamp=datetime(2024,1,1), 
                            trade_instructions=self.trade_instructions)
            
        with self.assertRaisesRegex(TypeError, "'trade_instructions' field must be of type list."):
            SignalEvent(timestamp=self.timestamp, trade_instructions=self.trade1)

        with self.assertRaisesRegex(TypeError, "All trade instructions must be instances of TradeInstruction."):
            SignalEvent(timestamp=self.timestamp, trade_instructions=["sell", "long"])

    # Constraint Check
    def test_value_constraints(self):
        with self.assertRaisesRegex(ValueError, "'trade_instructions' list cannot be empty."):
            SignalEvent(timestamp=self.timestamp,  trade_instructions=[])


if __name__ == "__main__":
    unittest.main()
