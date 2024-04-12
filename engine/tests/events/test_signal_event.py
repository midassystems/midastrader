import unittest
from datetime import datetime, timezone

from midas.events import OrderType, Action
from midas.events import TradeInstruction, SignalEvent

# TODO : Edge Cases

class TestTradeInsructions(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = 'AAPL'
        self.valid_order_type = OrderType.MARKET
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  5
        self.valid_weight = 0.483938
    
    # Basic Validation
    def test_valid_construction(self):
        instructions = TradeInstruction(ticker=self.valid_ticker,
                                        order_type=self.valid_order_type,
                                        action=self.valid_action,
                                        trade_id=self.valid_trade_id,
                                        leg_id=self.valid_leg_id,
                                        weight=self.valid_weight)

        self.assertEqual(instructions.ticker, self.valid_ticker)
        self.assertEqual(instructions.order_type, self.valid_order_type)
        self.assertEqual(instructions.action, self.valid_action)
        self.assertEqual(instructions.trade_id, self.valid_trade_id)
        self.assertEqual(instructions.leg_id, self.valid_leg_id)
        self.assertEqual(instructions.weight, self.valid_weight)

    # Type Check
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'ticker' must be a non-empty string."):
            TradeInstruction(ticker=1234,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)

    def test_order_type_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'order_type' must be of type OrderType enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type='MKT',
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_action_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'action' must be of type Action enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action='LONG',
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_trade_id_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id='2',
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_leg_id_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id='2',
                                weight=self.valid_weight)

    # Constraint Check
    def test_ticker_empty_constraint(self):
        with self.assertRaisesRegex(ValueError, "'ticker' must be a non-empty string."):
            TradeInstruction(ticker="",
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_order_type_none_validation(self):
        with self.assertRaisesRegex(ValueError, "'order_type' must be of type OrderType enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=None,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_action_none_validation(self):
        with self.assertRaisesRegex(ValueError, "'action' must be of type Action enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=None,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_trade_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=-1,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
            
    def test_trade_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=0,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight)
              
    def test_leg_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=-1,
                                weight=self.valid_weight)
            
    def test_leg_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=0,
                                weight=self.valid_weight)

class TestSignalEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timestamp = 1651500000
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
    def test_timestamp_type_valdiation(self):
        self.valid_timestamp = datetime(2024,1,1)
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int,"):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade_instructions)
    
    def test_trade_capital_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'trade_capital' must be of type float or int."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital='10000',trade_instructions=self.valid_trade_instructions)

    def test_trade_instructions_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'trade_instructions' must be of type list."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade1)
            
    def test_trade_instructions_item_type_valdiation(self):
        with self.assertRaisesRegex(TypeError, "All trade instructions must be instances of TradeInstruction."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital, trade_instructions=["sell", "long"])

    # Constraint Check
    def test_timestamp_format_valdiation(self):
        self.valid_timestamp = "01-01-2024"

        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int,"):
            signal = SignalEvent(timestamp=self.valid_timestamp,  trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade_instructions)
            
    def test_timestamp_none_valdiation(self):
        with self.assertRaisesRegex(TypeError, "'timestamp' should be in UNIX format of type float or int,"):
            signal = SignalEvent(timestamp=None, trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade_instructions)
    
    def test_trade_capital_constraint_valdiation(self):
        with self.assertRaisesRegex(ValueError, "'trade_capital' must be greater than zero."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital= -1000,trade_instructions=self.valid_trade_instructions)

        with self.assertRaisesRegex(ValueError, "'trade_capital' must be greater than zero."):
            signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital= 0,trade_instructions=self.valid_trade_instructions)

    def test_empty_trade_instructions_validation(self):
        with self.assertRaisesRegex(ValueError, "Trade instructions list cannot be empty."):
            signal = SignalEvent(timestamp=self.valid_timestamp,  trade_capital=self.valid_trade_capital, trade_instructions=[])

    def test_signal_serialization(self):
        signal = SignalEvent(timestamp=self.valid_timestamp, trade_capital=self.valid_trade_capital,  trade_instructions=self.valid_trade_instructions)
        serialized_timestamp = datetime.fromtimestamp(self.valid_timestamp, timezone.utc).isoformat()
        
        # Test
        signal_dict = signal.to_dict()

        # Validation
        self.assertEqual(signal_dict['timestamp'], serialized_timestamp) # cehck timestmap covnersin to ISOforamt when serialized
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
