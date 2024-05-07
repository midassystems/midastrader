import unittest
import numpy as np
from datetime import datetime, timezone

from midas.engine.events import SignalEvent
from midas.shared.orders import OrderType, Action
from midas.shared.signal import TradeInstruction

# TODO : Edge Cases
class TestSignalEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_trade_capital = 1000090
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]
                        
    # Basic Validation
    def test_valid_construction(self):
        # test
        signal = SignalEvent(self.valid_timestamp, self.valid_trade_capital, self.valid_trade_instructions)

        # Validate timestamp
        self.assertEqual(signal.timestamp,self.valid_timestamp)
        
        # Validate first set of trade instructions
        self.assertEqual(signal.trade_instructions[0].ticker, self.valid_trade1.ticker)
        self.assertEqual(signal.trade_instructions[0].order_type, self.valid_trade1.order_type)
        self.assertEqual(signal.trade_instructions[0].action, self.valid_trade1.action)
        self.assertEqual(signal.trade_instructions[0].trade_id, self.valid_trade1.trade_id)
        self.assertEqual(signal.trade_instructions[0].leg_id, self.valid_trade1.leg_id)
        self.assertEqual(signal.trade_instructions[0].weight, self.valid_trade1.weight)
        
        # Validate second set of trade instructions
        self.assertEqual(signal.trade_instructions[1].ticker, self.valid_trade2.ticker)
        self.assertEqual(signal.trade_instructions[1].order_type, self.valid_trade2.order_type)
        self.assertEqual(signal.trade_instructions[1].action, self.valid_trade2.action)
        self.assertEqual(signal.trade_instructions[1].trade_id, self.valid_trade2.trade_id)
        self.assertEqual(signal.trade_instructions[1].leg_id, self.valid_trade2.leg_id)
        self.assertEqual(signal.trade_instructions[1].weight, self.valid_trade2.weight)

    # Type Check
    def test_type_constraints(self):
        with self.assertRaisesRegex(TypeError, "timestamp must be of type np.uint64."):
            SignalEvent(timestamp=datetime(2024,1,1), 
                            trade_capital=self.valid_trade_capital, 
                            trade_instructions=self.valid_trade_instructions)
    
        with self.assertRaisesRegex(TypeError, "'trade_capital' must be of type float or int."):
            signal = SignalEvent(timestamp=self.valid_timestamp, 
                                 trade_capital='10000',
                                 trade_instructions=self.valid_trade_instructions)
            
        with self.assertRaisesRegex(TypeError, "'trade_instructions' must be of type list."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade1)

        with self.assertRaisesRegex(TypeError, "All trade instructions must be instances of TradeInstruction."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital, trade_instructions=["sell", "long"])

    # Constraint Check
    def test_value_constraints(self):
        with self.assertRaisesRegex(ValueError, "'trade_capital' must be greater than zero."):
            signal = SignalEvent(timestamp=self.valid_timestamp, 
                                 trade_capital= -1000,
                                 trade_instructions=self.valid_trade_instructions)

        with self.assertRaisesRegex(ValueError, "'trade_capital' must be greater than zero."):
            signal = SignalEvent(timestamp=self.valid_timestamp, 
                                 trade_capital= 0,
                                 trade_instructions=self.valid_trade_instructions)

        with self.assertRaisesRegex(ValueError, "Trade instructions list cannot be empty."):
            signal = SignalEvent(timestamp=self.valid_timestamp,  
                                 trade_capital=self.valid_trade_capital, 
                                 trade_instructions=[])

    def test_to_dict(self):
        signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital,  trade_instructions=self.valid_trade_instructions)
        serialized_timestamp = datetime.fromtimestamp(self.valid_timestamp, timezone.utc).isoformat()
        
        # Test
        signal_dict = signal.to_dict()

        # Validation
        self.assertEqual(signal_dict['timestamp'], self.valid_timestamp) 
        self.assertEqual(len(signal_dict['trade_instructions']), len(self.valid_trade_instructions)) # checkall trade instructions include in serialization

    # Edge Cases  
    # def test_future_timestamp_validation(self):
    #     future_timestamp = "3024-11-12T12:12:00"  # Clearly in the future
    #     with self.assertRaisesRegex(ValueError, "Timestamp cannot be in the future."):
    #         signal = Signal(timestamp=future_timestamp, trade_instructions=self.valid_trade_instructions)
    
    # def test_duplicate_trade_ids_validation(self):
    #     # Assuming trade_id should be unique within a Signal
    #     duplicate_trade = TradeInstruction(ticker='GOOG', order_type=OrderType.MARKET, action=Action.LONG, trade_id=2, leg_id=7, weight=0.3)
    #     with self.assertRaisesRegex(ValueError, "Duplicate trade_id detected."):
    #         signal = Signal(timestamp=self.valid_timestamp, trade_instructions=[self.valid_trade1, duplicate_trade])


if __name__ == "__main__":
    unittest.main()
