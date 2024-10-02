import unittest
from unittest.mock import MagicMock
from midas.engine.engine import EngineBuilder, Engine
from midas.engine.config import Mode


class TestEngineBuilder(unittest.TestCase):
    def test_construction(self):
        # Test
        engine = (
            EngineBuilder("tests/unit/engine/config.toml")
            .create_logger()  # Initialize logging
            .create_parameters()  # Load and parse the parameters
            .create_database_client()  # Set up the database client
            .create_symbols_map()  # Create the map for the trading symbols
            .create_core_components()  # Initialize order book, portfolio, etc.
            .create_gateways()  # Set up live or backtest gateways
            .create_observers()  # Set up the observer (for live trading)
            .build()  # Finalize the engine setup
        )

        # Validate
        self.assertIsInstance(engine, Engine)


class TestEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = (
            EngineBuilder("tests/unit/engine/config.toml")
            .create_logger()  # Initialize logging
            .create_parameters()  # Load and parse the parameters
            .create_database_client()  # Set up the database client
            .create_symbols_map()  # Create the map for the trading symbols
            .create_core_components()  # Initialize order book, portfolio, etc.
            .create_gateways()  # Set up live or backtest gateways
            .create_observers()  # Set up the observer (for live trading)
            .build()  # Finalize the engine setup
        )

    def test_initialize_live(self):
        self.engine.setup_live_environment = MagicMock()
        self.engine.set_strategy = MagicMock()
        self.engine.set_risk_model = MagicMock()

        # Test
        self.engine.config.mode = Mode.LIVE
        self.engine.initialize()

        # Validate
        self.assertTrue(self.engine.setup_live_environment.call_count, 1)
        self.assertTrue(self.engine.set_strategy.call_count, 1)
        self.assertTrue(self.engine.set_risk_model.call_count, 1)

    def test_initialize_backtest(self):
        self.engine.setup_backtest_environment = MagicMock()
        self.engine.set_strategy = MagicMock()
        self.engine.set_risk_model = MagicMock()

        # Test
        self.engine.config.mode = Mode.BACKTEST
        self.engine.initialize()

        # Validate
        self.assertTrue(self.engine.setup_backtest_environment.call_count == 1)
        self.assertTrue(self.engine.set_strategy.call_count == 1)
        self.assertTrue(self.engine.set_risk_model.call_count == 1)

    def test_start_live(self):
        self.engine._run_live_event_loop = MagicMock()
        self.engine.logger.info = MagicMock()

        # Test
        self.engine.config.mode = Mode.LIVE
        self.engine.start()

        # Validate
        self.assertTrue(self.engine._run_live_event_loop.call_count == 1)

    def test_start_backtest(self):
        self.engine._run_backtest_event_loop = MagicMock()
        self.engine.logger.info = MagicMock()

        # Test
        self.engine.config.mode = Mode.BACKTEST
        self.engine.start()

        # Validate
        self.assertTrue(self.engine._run_backtest_event_loop.call_count == 1)


if __name__ == "__main__":
    unittest.main()
