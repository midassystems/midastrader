import unittest
from midastrader.cli import run


class MidasBacktestIntegration(unittest.TestCase):
    def test_backtest(self):
        run("tests/integration/strategy/config.toml", "backtest")


if __name__ == "__main__":
    unittest.main()
