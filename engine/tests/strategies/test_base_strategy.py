import unittest
from unittest.mock import Mock
from unittest.mock import patch

from engine.strategies import BaseStrategy
from engine.events import BarData, MarketEvent, SignalEvent
from engine.events import  SignalEvent, MarketEvent, TradeInstruction, Action, OrderType

# TODO: Edge case testing

class TestStrategy(BaseStrategy):
    def prepare(self):
        pass

    def handle_market_data(self):
        pass

    def _entry_signal(self):
        pass

    def _exit_signal(self):
        pass

    def _asset_allocation(self):
        pass

class TestTestStrategy(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        self.test_strategy = TestStrategy(portfolio_server=self.mock_portfolio_server,order_book=self.mock_order_book, 
                                          logger = self.mock_portfolio_server, event_queue=self.mock_event_queue)

        # Test Data
        self.valid_timestamp = 1651500000
        self.valid_trade_capital = 1000000

        self.valid_bar = BarData(timestamp = self.valid_timestamp,
                        open = 80.90,
                        close = 9000.90,
                        high = 75.90,
                        low = 8800.09,
                        volume = 880000)
        self.valid_market_event = MarketEvent(data={'AAPL': self.valid_bar}, 
                                                timestamp=self.valid_timestamp)
        
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
    def test_on_market_data(self):
        with patch.object(self.test_strategy, 'handle_market_data') as mocked_method:
            self.test_strategy.on_market_data(self.valid_market_event)
            mocked_method.assert_called_once() # check handle market_data called
        
    def test_set_signal(self):
        # Test
        self.test_strategy.set_signal(self.valid_trade_instructions, self.valid_trade_capital, self.valid_timestamp)

        # Validation
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.") # check that event_queue.put() was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0] # Get the argument with which event_queue.put was called
        self.assertIsInstance(called_with_arg, SignalEvent, "The argument is not an instance of SignalEvent")

    # Type Validation
    def test_on_market_data_invalid_event(self):
        # Test invalid event type
        with self.assertRaisesRegex(TypeError, "'event' must be of type Market Event instance." ):
            self.test_strategy.on_market_data("Not_market_event")

    def test_create_signal_event_invalid_trade_instructions(self):
        # Test failure to create signal event
        with self.assertRaisesRegex(RuntimeError, "Failed to create or queue SignalEvent due to input error"):
            self.test_strategy.set_signal([], self.valid_trade_capital, self.valid_timestamp)

if __name__ == "__main__":
    unittest.main()