import unittest
import numpy as np
import pandas as pd
from decimal import Decimal
from midas.shared.market_data import BarData
from midas.shared.signal import TradeInstruction
from unittest.mock import Mock, patch, MagicMock
from midas.shared.orders import Action, OrderType
from midas.engine.events import  SignalEvent, MarketEvent
from midas.engine.strategies import BaseStrategy, load_strategy_class


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

    def get_strategy_data(self) -> pd.DataFrame:
        pass

class TestTestStrategy(unittest.TestCase):
    def setUp(self) -> None:
        # Mock method
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()

        # Test strategy instance
        self.test_strategy = TestStrategy(portfolio_server=self.mock_portfolio_server,order_book=self.mock_order_book, 
                                          logger = self.mock_portfolio_server, event_queue=self.mock_event_queue)

        # Test Data
        self.ticker="AAPL"
        self.trade_capital = 1000000
        self.timestamp = np.uint64(1707221160000000000)
        self.bar = BarData(ticker=self.ticker,
                        timestamp = self.timestamp,
                        open = Decimal(80.90),
                        close = Decimal(9000.90),
                        high = Decimal(75.90),
                        low = Decimal(8800.09),
                        volume = np.uint64(880000))
        
        self.market_event = MarketEvent(data={'AAPL': self.bar}, 
                                                timestamp=self.timestamp)
        
        self.trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=2)
        self.trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5,
                                                quantity=2)
        self.trade_instructions = [self.trade1,self.trade2]

    # Basic Validation
    def test_on_market_data(self):
        with patch.object(self.test_strategy, 'handle_market_data') as mocked_method:
            self.test_strategy.on_market_data(self.market_event)
            mocked_method.assert_called_once() # check handle market_data called
        
    def test_set_signal(self):
        # Test
        self.test_strategy.set_signal(self.trade_instructions, self.timestamp)

        # Validate
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.")
        # Get the argument with which event_queue.put was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0]
        self.assertIsInstance(called_with_arg, SignalEvent, "The argument is not an instance of SignalEvent")

    # Type Validation
    def test_on_market_data_invalid_event(self):
        with self.assertRaisesRegex(TypeError, "'event' must be of type Market Event instance." ):
            self.test_strategy.on_market_data("Not_market_event")

    def test_create_signal_event_invalid_trade_instructions(self):
        with self.assertRaisesRegex(RuntimeError, "Failed to create or queue SignalEvent due to input error"):
            self.test_strategy.set_signal([], self.timestamp)

class TestLoadStrategyClass(unittest.TestCase):

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_strategy_class_success(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module and class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module.TestStrategy = TestStrategy
        mock_module_from_spec.return_value = mock_module

        # Test
        strategy_class = load_strategy_class('fake/path/to/module.py', 'TestStrategy')

        # Validate
        self.assertEqual(strategy_class, TestStrategy)

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_strategy_class_class_not_found(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module without the class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module_from_spec.return_value = mock_module

        # Test
        with self.assertRaises(TypeError):
            load_strategy_class('fake/path/to/module.py',"BaseStrategy")

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_strategy_class_not_subclass(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module with class that is not a subclass of BaseStrategy
        class NotStrategy:
            pass

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module.NotStrategy = NotStrategy
        mock_module_from_spec.return_value = mock_module

        # Test
        with self.assertRaises(ValueError):
            load_strategy_class('fake/path/to/module.py', 'NotStrategy')

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_strategy_class_invalid_module_path(self, mock_module_from_spec, mock_spec_from_file_location):
        # Simulate an ImportError when trying to load the module
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_spec.loader.exec_module.side_effect = ImportError("Cannot load module")

        # Test
        with self.assertRaises(ImportError):
            load_strategy_class('invalid/path/to/module.py', 'TestStrategy')


if __name__ == "__main__":
    unittest.main()