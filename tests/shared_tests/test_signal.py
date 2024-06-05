import unittest

from midas.shared.orders import OrderType, Action
from midas.shared.signal import TradeInstruction

# TODO : Edge Cases

class TestTradeInsructions(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_ticker = 'AAPL'
        self.valid_order_type = OrderType.MARKET
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  5
        self.valid_weight = 0.483938
        self.valid_quantity = -10
        self.valid_limit_price = 100
        self.valid_aux_price = 10
    
    # Basic Validation
    def test_valid_construction_market_order(self):
        # test
        instructions = TradeInstruction(ticker=self.valid_ticker,
                                        order_type=self.valid_order_type,
                                        action=self.valid_action,
                                        trade_id=self.valid_trade_id,
                                        leg_id=self.valid_leg_id,
                                        weight=self.valid_weight,
                                        quantity=self.valid_quantity)
        # validate
        self.assertEqual(instructions.ticker, self.valid_ticker)
        self.assertEqual(instructions.order_type, self.valid_order_type)
        self.assertEqual(instructions.action, self.valid_action)
        self.assertEqual(instructions.trade_id, self.valid_trade_id)
        self.assertEqual(instructions.leg_id, self.valid_leg_id)
        self.assertEqual(instructions.weight, self.valid_weight)
        self.assertEqual(instructions.quantity, self.valid_quantity)

    def test_valid_construction_limit_order(self):
        # test
        instructions = TradeInstruction(ticker=self.valid_ticker,
                                        order_type=OrderType.LIMIT,
                                        action=self.valid_action,
                                        trade_id=self.valid_trade_id,
                                        leg_id=self.valid_leg_id,
                                        weight=self.valid_weight,
                                        quantity=self.valid_quantity,
                                        limit_price=self.valid_limit_price)
        # validate
        self.assertEqual(instructions.ticker, self.valid_ticker)
        self.assertEqual(instructions.order_type, OrderType.LIMIT)
        self.assertEqual(instructions.action, self.valid_action)
        self.assertEqual(instructions.trade_id, self.valid_trade_id)
        self.assertEqual(instructions.leg_id, self.valid_leg_id)
        self.assertEqual(instructions.weight, self.valid_weight)
        self.assertEqual(instructions.quantity, self.valid_quantity)
        self.assertEqual(instructions.limit_price, self.valid_limit_price)
    
    def test_valid_construction_stop_loss(self):
        # test
        instructions = TradeInstruction(ticker=self.valid_ticker,
                                        order_type=OrderType.STOPLOSS,
                                        action=self.valid_action,
                                        trade_id=self.valid_trade_id,
                                        leg_id=self.valid_leg_id,
                                        weight=self.valid_weight,
                                        quantity=self.valid_quantity,
                                        aux_price=self.valid_aux_price)
        # validate
        self.assertEqual(instructions.ticker, self.valid_ticker)
        self.assertEqual(instructions.order_type, OrderType.STOPLOSS)
        self.assertEqual(instructions.action, self.valid_action)
        self.assertEqual(instructions.trade_id, self.valid_trade_id)
        self.assertEqual(instructions.leg_id, self.valid_leg_id)
        self.assertEqual(instructions.weight, self.valid_weight)
        self.assertEqual(instructions.quantity, self.valid_quantity)
        self.assertEqual(instructions.aux_price, self.valid_aux_price)

    # Type Check
    def test_ticker_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'ticker' must be a non-empty string."):
            TradeInstruction(ticker=1234,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)

    def test_order_type_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'order_type' must be of type OrderType enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type='MKT',
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_action_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'action' must be of type Action enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action='LONG',
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_trade_id_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id='2',
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_leg_id_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id='2',
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
    
    def test_quantity_type_validation(self):
        with self.assertRaisesRegex(ValueError, "'quantity' must be an int or float."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=2,
                                weight=self.valid_weight,
                                quantity="123")

    # Constraint Check
    def test_ticker_empty_constraint(self):
        with self.assertRaisesRegex(ValueError, "'ticker' must be a non-empty string."):
            TradeInstruction(ticker="",
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_order_type_none_validation(self):
        with self.assertRaisesRegex(ValueError, "'order_type' must be of type OrderType enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=None,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_action_none_validation(self):
        with self.assertRaisesRegex(ValueError, "'action' must be of type Action enum."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=None,
                                trade_id=self.valid_trade_id,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_trade_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=-1,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_trade_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'trade_id' must be a non-negative integer"):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=0,
                                leg_id=self.valid_leg_id,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
              
    def test_leg_id_negative_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=-1,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_leg_id_zero_validation(self):
        with self.assertRaisesRegex(ValueError, "'leg_id' must be a non-negative integer."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=self.valid_order_type,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=0,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)

    def test_limit_order_limit_price_constraint(self):
        with self.assertRaisesRegex(ValueError, "'limit_price' cannot be None for OrderType.LIMIT."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=OrderType.LIMIT,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=1,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)
            
    def test_stop_order_aux_price_constraint(self):
        with self.assertRaisesRegex(ValueError, "'aux_price' cannot be None for OrderType.STOPLOSS."):
            TradeInstruction(ticker=self.valid_ticker,
                                order_type=OrderType.STOPLOSS,
                                action=self.valid_action,
                                trade_id=self.valid_trade_id,
                                leg_id=1,
                                weight=self.valid_weight,
                                quantity=self.valid_quantity)


if __name__ == "__main__":
    unittest.main()
