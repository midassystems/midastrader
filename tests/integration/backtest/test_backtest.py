import unittest
from midas.cli import run


class MidasBacktestIntegration(unittest.TestCase):
    def test_backtest(self):
        run("tests/integration/strategy/config.toml")


if __name__ == "__main__":
    unittest.main()
