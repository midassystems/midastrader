import unittest

from .backtest.main import main

class MidasBacktestIntegration(unittest.TestCase):
    def test_backtest(self):
        main() # run full backtest
    
if __name__ == "__main__":
    unittest.main()