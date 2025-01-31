import unittest
from unittest.mock import MagicMock

from midastrader.config import Mode
from midastrader.engine import EngineBuilder, Engine


class TestEngineBuilder(unittest.TestCase):
    def test_construction(self):
        # Test
        engine = EngineBuilder("tests/unit/config.toml", Mode.BACKTEST).build()

        # Validate
        self.assertIsInstance(engine, Engine)


class TestEngineBacktest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EngineBuilder(
            "tests/unit/config.toml", Mode.BACKTEST
        ).build()

    def test_initialize_backtest(self):
        self.engine.core_engine.set_strategy = MagicMock()
        self.engine.core_engine.set_risk_model = MagicMock()

        # Test
        self.engine.mode = Mode.BACKTEST
        self.engine.initialize()

        # Validate
        self.assertTrue(self.engine.core_engine.set_strategy.call_count, 1)
        self.assertTrue(self.engine.core_engine.set_risk_model, 1)

    def test_start_backtest(self):
        self.engine._backtest_loop = MagicMock()
        self.engine.logger.info = MagicMock()
        self.engine.core_engine.start = MagicMock()
        self.engine.data_engine.start = MagicMock()
        self.engine.execution_engine.start = MagicMock()
        self.engine.core_engine.running.set()
        self.engine.data_engine.running.set()
        self.engine.execution_engine.running.set()

        # Test
        self.engine.mode = Mode.BACKTEST
        self.engine.start()

        # Validate
        self.assertTrue(self.engine._backtest_loop.call_count == 1)


class TestEngineLive(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EngineBuilder(
            "tests/unit/config.toml", Mode.LIVE
        ).build()

    def test_initialize_live(self):
        self.engine.core_engine.set_strategy = MagicMock()
        self.engine.core_engine.set_risk_model = MagicMock()

        # Test
        self.engine.mode = Mode.LIVE
        self.engine.initialize()

        # Validate
        self.assertTrue(self.engine.core_engine.set_strategy.call_count, 1)
        self.assertTrue(self.engine.core_engine.set_risk_model, 1)

    def test_start_live(self):
        self.engine._live_loop = MagicMock()
        self.engine.logger.info = MagicMock()
        self.engine.core_engine.start = MagicMock()
        self.engine.data_engine.start = MagicMock()
        self.engine.execution_engine.start = MagicMock()
        self.engine.core_engine.running.set()
        self.engine.data_engine.running.set()
        self.engine.execution_engine.running.set()

        # Test
        self.engine.mode = Mode.LIVE
        self.engine.start()

        # Validate
        self.assertTrue(self.engine._live_loop.call_count == 1)


if __name__ == "__main__":
    unittest.main()
