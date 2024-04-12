import unittest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from midas.performance.statistics import PerformanceStatistics

# TODO: edge cases
class TestPerformancStatistics(unittest.TestCase):    
    def setUp(self):
        # Sample equity curve and trade log for testing
        self.equity_curve = np.array([100, 105, 103, 110, 108])
        self.benchmark_equity_curve = np.array([100, 103, 102, 106, 108])
        
        self.trade_log = pd.DataFrame({
            'pnl': [20, -10, 15, -5, 30, -20],
            'gain/loss': [0.10, -0.05, 0.075, -0.25, 0.15, -0.010]
        })
    
    # Net Profit
    def test_net_profit(self):
        expected_net_profit = 30  # Expected result based on the sample trade log
        net_profit = PerformanceStatistics.net_profit(self.trade_log)
        self.assertEqual(net_profit, expected_net_profit)

    def test_net_profit_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.net_profit([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.net_profit(pd.DataFrame())

    def test_net_profit_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.net_profit(trade_log), 0)

    # Daily Return
    def test_period_return(self):
        expected_daily_returns = np.array([0.05, -0.019, 0.0679, -0.0182])
        daily_returns = PerformanceStatistics.period_return(self.equity_curve)
        np.testing.assert_array_almost_equal(daily_returns, expected_daily_returns, decimal=4)

    def test_period_return_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.period_return([10, -5, 15])
    
    def test_period_return_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.period_return(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 1)  # Expecting an array with a single zero

    # Cumulative Return
    def test_cumulative_return(self):
        expected_cumulative_returns = np.array([0.05, 0.03, 0.10, 0.08])
        cumulative_returns = PerformanceStatistics.cumulative_return(self.equity_curve)
        np.testing.assert_array_almost_equal(cumulative_returns, expected_cumulative_returns, decimal=4)
        
    def test_cumulative_return_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.cumulative_return([10, -5, 15])
    
    def test_cumulative_return_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.cumulative_return(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 1)  # Expecting an array with a single zero

    # Total Return
    def test_total_return(self):
        expected_total_return = 0.08  # Expected result based on the sample equity curve
        total_return = PerformanceStatistics.total_return(self.equity_curve)
        self.assertEqual(total_return, expected_total_return)

    def test_total_return_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.total_return([10, -5, 15])
    
    def test_total_return_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.total_return(equity_curve)
        self.assertEqual(result, 0)  # Expecting an array with a single zero

    # Drawdown
    def test_drawdown(self):
        expected_drawdowns = np.array([0, 0, -0.01914, 0, -0.01818])
        drawdowns = PerformanceStatistics.drawdown(self.equity_curve)
        np.testing.assert_array_almost_equal(drawdowns, expected_drawdowns, decimal=4)

    def test_drawdown_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.drawdown([10, -5, 15])
    
    def test_drawdown_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.drawdown(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 1)  # Expecting an array with a single zero

    def test_max_drawdown(self):
        expected_max_drawdown = -0.019  # Expected result based on the sample equity curve
        max_drawdown = PerformanceStatistics.max_drawdown(self.equity_curve)
        self.assertEqual(max_drawdown, expected_max_drawdown)

    def test_max_drawdown_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.max_drawdown([10, -5, 15])
    
    def test_max_drawdown_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.drawdown(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result, 0)  # Expecting an array with a single zero

    # Standard Deviation
    def test_annual_standard_deviation(self):
        # Calculate expected annual standard deviation manually or adjust according to your data
        expected_annual_std_dev = np.std(self.equity_curve, ddof=1) * np.sqrt(252)
        annual_std_dev = PerformanceStatistics.annual_standard_deviation(self.equity_curve)
        self.assertAlmostEqual(annual_std_dev, expected_annual_std_dev, places=4)

    def test_annual_standard_deviation_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.annual_standard_deviation([10, -5, 15])
    
    def test_annual_standard_deviation_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.annual_standard_deviation(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result, 0)  # Expecting an array with a single zero

    # Total Trades
    def test_total_trades(self):
        expected_total_trades = 6
        total_trades = PerformanceStatistics.total_trades(self.trade_log)
        self.assertEqual(total_trades, expected_total_trades)

    # Total Winning Trades
    def test_total_winning_trades(self):
        expected_winning_trades = 3
        total_winning_trades = PerformanceStatistics.total_winning_trades(self.trade_log)
        self.assertEqual(total_winning_trades, expected_winning_trades)

    def test_total_winning_trades_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.total_winning_trades([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.total_winning_trades(pd.DataFrame())

    def test_total_winning_trades_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.total_winning_trades(trade_log), 0)
    
    # Total Losing Trades
    def test_total_losing_trades(self):
        expected_losing_trades = 3
        total_losing_trades = PerformanceStatistics.total_losing_trades(self.trade_log)
        self.assertEqual(total_losing_trades, expected_losing_trades)

    def test_total_losing_trades_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.total_losing_trades([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.total_losing_trades(pd.DataFrame())

    def test_total_losing_trades_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.total_losing_trades(trade_log), 0)
    
    # Total Avg Win Percent
    def test_avg_win_return_rate(self):
        expected_avg_win = 0.108333  # Based on the provided gain/loss values
        avg_win_return_rate = PerformanceStatistics.avg_win_return_rate(self.trade_log)
        self.assertAlmostEqual(avg_win_return_rate, expected_avg_win, places=4)

    def test_avg_win_return_rate_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.avg_win_return_rate([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.avg_win_return_rate(pd.DataFrame())

    def test_avg_win_return_rate_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.avg_win_return_rate(trade_log), 0)
    
    # Total avg_loss_return_rate
    def test_avg_loss_return_rate(self):
        expected_avg_loss = -0.10333  # Based on the provided gain/loss values
        avg_loss_return_rate = PerformanceStatistics.avg_loss_return_rate(self.trade_log)
        self.assertAlmostEqual(avg_loss_return_rate, expected_avg_loss, places=4)

    def test_avg_loss_return_rate_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.avg_loss_return_rate([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.avg_loss_return_rate(pd.DataFrame())

    def test_avg_loss_return_rate_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.avg_loss_return_rate(trade_log), 0)

    # Percent Profitable
    def test_profitability_ratio(self):
        expected_profitability_ratio = 0.50  # 3 winning trades out of 6 total trades
        profitability_ratio = PerformanceStatistics.profitability_ratio(self.trade_log)
        self.assertEqual(profitability_ratio, expected_profitability_ratio)

    def test_profitability_ratio_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.profitability_ratio([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.profitability_ratio(pd.DataFrame())

    def test_profitability_ratio_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.profitability_ratio(trade_log), 0)

    # Avg Trade Profit
    def test_avg_trade_profit(self):
        expected_avg_trade_profit = 5  # (20-10+15-5+30-20) / 6
        average_trade_profit = PerformanceStatistics.avg_trade_profit(self.trade_log)
        self.assertEqual(average_trade_profit, expected_avg_trade_profit)

    def test_avg_trade_profit_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.avg_trade_profit([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.avg_trade_profit(pd.DataFrame())

    def test_avg_trade_profit_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.avg_trade_profit(trade_log), 0)

    # Profit Factor
    def test_profit_factor(self):
        expected_profit_factor = 1.8571 # (20+15+30) / abs(-10-5-20)
        profit_factor = PerformanceStatistics.profit_factor(self.trade_log)
        self.assertEqual(profit_factor, expected_profit_factor)

    def test_profit_factor_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.profit_factor([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.profit_factor(pd.DataFrame())

    def test_profit_factor_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.profit_factor(trade_log), 0)

    # Profit & Loss Ratio
    def test_profit_and_loss_ratio(self):
        expected_pnl_ratio = 1.8571  # abs(mean([20,15,30]) / mean([-10,-5,-20]))
        profit_and_loss_ratio = PerformanceStatistics.profit_and_loss_ratio(self.trade_log)
        self.assertEqual(profit_and_loss_ratio, expected_pnl_ratio)

    def test_profit_and_loss_ratio_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.profit_and_loss_ratio([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.profit_and_loss_ratio(pd.DataFrame())

    def test_profit_and_loss_ratio_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'pnl': []})
        self.assertEqual(PerformanceStatistics.profit_and_loss_ratio(trade_log), 0)

   # Sortino Ratio
    def test_sortino_ratio(self):
        target_return = 0
        negative_returns = self.trade_log[self.trade_log['gain/loss'] < target_return]['gain/loss'] # Filter for negative returns
        expected_return = self.trade_log['gain/loss'].mean() # Calculate expected return as average return since target return is 0
        downside_deviation = negative_returns.std(ddof=1) # Calculate downside deviation (standard deviation of negative returns)
        # Calculate expected Sortino ratio
        if downside_deviation > 0:
            expected_sortino_ratio = expected_return / downside_deviation
        else:
            expected_sortino_ratio = 0.0

        sortino_ratio = PerformanceStatistics.sortino_ratio(self.trade_log)
        self.assertAlmostEqual(sortino_ratio, expected_sortino_ratio, places=4)

    def test_sortino_ratio_type_check(self):        
        # Test with incorrect type (should raise an error or handle gracefully)
        with self.assertRaises(TypeError):
            PerformanceStatistics.sortino_ratio([10, -5, 15])

        # Test with missing column
        with self.assertRaises(ValueError):
            PerformanceStatistics.sortino_ratio(pd.DataFrame())

    def test_sortino_ratio_null_handling(self):
        # Test with empty DataFrame
        trade_log = pd.DataFrame({'gain/loss': []})
        self.assertEqual(PerformanceStatistics.sortino_ratio(trade_log), 0)

   # Sharpe Ratio
    def test_sharpe_ratio(self):
        daily_returns = np.diff(self.equity_curve) / self.equity_curve[:-1] # Calculate daily returns
        risk_free_rate_daily = 0.04 / 252 # Risk-free rate adjustment for daily returns
        excess_returns = daily_returns - risk_free_rate_daily # Excess returns calculation
        expected_sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns, ddof=1) if np.std(excess_returns, ddof=1) != 0 else 0 # Expected Sharpe ratio calculation

        sharpe_ratio = PerformanceStatistics.sharpe_ratio(self.equity_curve)
        self.assertAlmostEqual(sharpe_ratio, expected_sharpe_ratio, places=3)

    def test_sharpe_ratio_type_check(self):
        with self.assertRaises(TypeError):
            PerformanceStatistics.sharpe_ratio([10, -5, 15])
    
    def test_sharpe_ratio_null_handling(self):
        # Test with empty input
        list = []
        equity_curve = np.array(list)
        result = PerformanceStatistics.sharpe_ratio(equity_curve)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result, 0)  # Expecting an array with a single zero


if __name__ == "__main__":
    unittest.main()