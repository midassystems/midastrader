import unittest
from unittest.mock import Mock, patch

from midas.shared.backtest import Backtest

# #TODO: edge cases
class TestBacktest(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": "2018-05-18", 
                                "train_end": "2023-01-19", 
                                "test_start": "2023-01-19", 
                                "test_end": "2024-01-19", 
                                "tickers": ["AAPL"], 
                                "benchmark": ["^GSPC"]
                            }
        self.mock_static_stats = [{
                                "net_profit": 330.0, 
                                "total_fees": 40.0, 
                                "total_return": 0.33, 
                                "ending_equity": 1330.0, 
                                "max_drawdown": 0.0, 
                                "total_trades": 2, 
                                "num_winning_trades": 2, 
                                "num_lossing_trades": 0, 
                                "avg_win_percent": 0.45, 
                                "avg_loss_percent": 0, 
                                "percent_profitable": 1.0, 
                                "profit_and_loss": 0.0, 
                                "profit_factor": 0.0, 
                                "avg_trade_profit": 165.0, 
                                "sortino_ratio": 0.0
                            }]
        self.mock_timeseries_stats =  [
                                {
                                    "timestamp": "2023-12-09T12:00:00Z",
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": "2023-12-10T12:00:00Z",
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.087", 
                                    "daily_benchmark_return": "0.009"
                                }
                            ]
        self.mock_trades =  [{
                                "trade_id": 1, 
                                "leg_id": 1, 
                                "timestamp": "2023-01-03T00:00:00+0000", 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "price": 130.74, 
                                "cost": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.mock_signals =  [{
                                "timestamp": "2023-01-03T00:00:00+0000", 
                                "trade_instructions": [{
                                    "ticker": "AAPL", 
                                    "action": "BUY", 
                                    "trade_id": 1, 
                                    "leg_id": 1, 
                                    "weight": 0.05
                                }, 
                                {
                                    "ticker": "MSFT", 
                                    "action": "SELL", 
                                    "trade_id": 1, 
                                    "leg_id": 2, 
                                    "weight": 0.05
                                }]
                            }]
        
        self.backtest = Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 period_timeseries_stats = self.mock_timeseries_stats,
                                 daily_timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)

    # Basic Validation
    def test_to_dict(self):
        # test
        backtest_dict = self.backtest.to_dict()

        # validate
        self.assertEqual(backtest_dict['parameters'], self.mock_parameters)
        self.assertEqual(backtest_dict['static_stats'], self.mock_static_stats)
        self.assertEqual(backtest_dict['period_timeseries_stats'], self.mock_timeseries_stats)
        self.assertEqual(backtest_dict['daily_timeseries_stats'], self.mock_timeseries_stats)
        self.assertEqual(backtest_dict['signals'], self.mock_signals)
        self.assertEqual(backtest_dict['trades'], self.mock_trades)

    def test_type_constraints(self):
        with self.assertRaisesRegex(ValueError, "parameters must be a dictionary"):
            Backtest(parameters = "self.mock_parameters,",
                                static_stats = self.mock_static_stats,
                                period_timeseries_stats = self.mock_timeseries_stats,
                                daily_timeseries_stats = self.mock_timeseries_stats,
                                trade_data = self.mock_trades,
                                signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError,"static_stats must be a list of dictionaries" ):
            Backtest(parameters = self.mock_parameters,
                                static_stats = "self.mock_static_stats",
                                period_timeseries_stats = self.mock_timeseries_stats,
                                daily_timeseries_stats = self.mock_timeseries_stats,
                                trade_data = self.mock_trades,
                                signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "period_timeseries_stats must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 period_timeseries_stats = "self.mock_timeseries_stats,",
                                 daily_timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)

        with self.assertRaisesRegex(ValueError, "daily_timeseries_stats must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 period_timeseries_stats = self.mock_timeseries_stats,
                                 daily_timeseries_stats = "self.mock_timeseries_stats",
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "trade_data must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 period_timeseries_stats = self.mock_timeseries_stats,
                                 daily_timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = "self.mock_trades",
                                 signal_data = self.mock_signals)
            
        with self.assertRaisesRegex(ValueError, "signal_data must be a list of dictionaries"):
            Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 period_timeseries_stats = self.mock_timeseries_stats,
                                 daily_timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = "self.mock_signals")

if __name__ == "__main__":
    unittest.main()

