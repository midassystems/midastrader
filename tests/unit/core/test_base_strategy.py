import unittest
import pandas as pd
import time
import threading
from mbn import OhlcvMsg
from unittest.mock import Mock, patch, MagicMock

from midastrader.structs import SignalInstruction, Action, OrderType
from midastrader.structs.events import SignalEvent, MarketEvent
from midastrader.utils.logger import SystemLogger
from midastrader.core.adapters.base_strategy import (
    BaseStrategy,
    load_strategy_class,
)
from midastrader.message_bus import MessageBus, EventType


class TestStrategy(BaseStrategy):
    def handle_event(self, event: MarketEvent) -> None:
        pass

    def get_strategy_data(self) -> pd.DataFrame:
        return pd.DataFrame()


class TestTestStrategy(unittest.TestCase):
    def setUp(self) -> None:
        # Mock method
        self.symbols_map = Mock()
        self.historical_data = Mock()
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_portfolio_server = Mock()

        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # Test strategy instance
        self.bus = MessageBus()
        self.test_strategy = TestStrategy(self.symbols_map, self.bus)
        threading.Thread(
            target=self.test_strategy.process, daemon=True
        ).start()

        # Test Data
        self.ticker = "AAPL"
        self.trade_capital = 1000000
        self.timestamp = 1707221160000000000

        self.bar = OhlcvMsg(
            instrument_id=1,
            ts_event=self.timestamp,
            rollover_flag=0,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        self.market_event = MarketEvent(self.timestamp, self.bar)

        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            signal_id=2,
            weight=0.5,
            quantity=2.0,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            signal_id=2,
            weight=0.5,
            quantity=2.0,
        )
        self.trade_instructions = [self.trade1, self.trade2]

    # Basic Validation
    def test_process(self):
        self.timestamp = 1707221160000000000
        self.bar = OhlcvMsg(
            instrument_id=1,
            rollover_flag=0,
            ts_event=self.timestamp,
            open=int(80.90 * 1e9),
            close=int(9000.90 * 1e9),
            high=int(75.90 * 1e9),
            low=int(8800.09 * 1e9),
            volume=880000,
        )

        event = MarketEvent(timestamp=self.timestamp, data=self.bar)

        # Test
        self.test_strategy.handle_event = MagicMock()
        self.bus.publish(EventType.ORDER_BOOK, event)
        time.sleep(1)

        # Validate
        args = self.test_strategy.handle_event.call_args[0]
        self.assertEqual(args[0], event)

    def test_set_signal(self):
        self.bus.publish = MagicMock()

        # Test
        self.test_strategy.set_signal(self.trade_instructions, self.timestamp)

        # Validate
        self.assertEqual(self.bus.publish.call_count, 2)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.SIGNAL)
        self.assertEqual(
            first_call_args[1],
            SignalEvent(self.timestamp, self.trade_instructions),
        )

        # Validate the second call
        second_call_args = calls[1][0]
        # Replace with your expected arguments for the second call
        self.assertEqual(second_call_args[0], EventType.SIGNAL_UPDATE)
        self.assertEqual(
            second_call_args[1],
            SignalEvent(self.timestamp, self.trade_instructions),
        )

    def test_set_system_updated(self):
        self.bus.publish = MagicMock()

        # Test
        self.test_strategy.set_signal([], self.timestamp)

        # Validate
        self.assertEqual(self.bus.topics[EventType.UPDATE_SYSTEM], False)


class TestLoadStrategyClass(unittest.TestCase):

    @patch("importlib.util.spec_from_file_location")
    @patch("importlib.util.module_from_spec")
    def test_load_strategy_class_success(
        self, mock_module_from_spec, mock_spec_from_file_location
    ):
        # Mock module and class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module.TestStrategy = TestStrategy
        mock_module_from_spec.return_value = mock_module

        # Test
        strategy_class = load_strategy_class(
            "fake/path/to/module.py", "TestStrategy"
        )

        # Validate
        self.assertEqual(strategy_class, TestStrategy)

    @patch("importlib.util.spec_from_file_location")
    @patch("importlib.util.module_from_spec")
    def test_load_strategy_class_class_not_found(
        self, mock_module_from_spec, mock_spec_from_file_location
    ):
        # Mock module without the class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module_from_spec.return_value = mock_module

        # Test
        with self.assertRaises(TypeError):
            load_strategy_class("fake/path/to/module.py", "BaseStrategy")

    @patch("importlib.util.spec_from_file_location")
    @patch("importlib.util.module_from_spec")
    def test_load_strategy_class_not_subclass(
        self, mock_module_from_spec, mock_spec_from_file_location
    ):
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
            load_strategy_class("fake/path/to/module.py", "NotStrategy")

    @patch("importlib.util.spec_from_file_location")
    @patch("importlib.util.module_from_spec")
    def test_load_strategy_class_invalid_module_path(
        self, mock_module_from_spec, mock_spec_from_file_location
    ):
        # Simulate an ImportError when trying to load the module
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_spec.loader.exec_module.side_effect = ImportError(
            "Cannot load module"
        )

        # Test
        with self.assertRaises(ImportError):
            load_strategy_class("invalid/path/to/module.py", "TestStrategy")


if __name__ == "__main__":
    unittest.main()
