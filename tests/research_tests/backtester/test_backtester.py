import unittest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from pandas.testing import assert_frame_equal

from midas.research.strategy import BaseStrategy
from midas.research.backtester.backtester import VectorizedBacktest

# TODO : edge cases /integration

class TestVectorizedBacktest(unittest.TestCase):
    def setUp(self):
        # Mock data
        data = {
                'timestamp': [
                    # 1700064000000000000, 1700067600000000000, 1700071200000000000,
                    # 1700074800000000000, 1700143200000000000, 1700146800000000000,
                    # 1700150400000000000, 1700154000000000000, 1700157600000000000,
                    
                    1700161200000000000, 1700247600000000000, 1700334000000000000,
                    1700420400000000000, 1700506800000000000, 1700593200000000000,
                    1700852400000000000, 1700938800000000000, 1701025200000000000,
                    1701111600000000000

                ],
                'A': [75.600, 75.300, 74.900, 74.925, 74.250, 74.425, 75.400, 75.075, 75.600,  75.500],
                'B': [489.25, 487.00, 487.75, 489.25, 485.25, 485.50, 491.50, 493.00, 493.00, 492.50],
        }
        self.mock_data = pd.DataFrame(data)
        self.mock_data.set_index('timestamp', inplace=True)

        # Symbols Map
        self.symbols_map = {'A': {'quantity_multiplier': 40000, 'price_multiplier': 0.01}, 'B':{'quantity_multiplier': 5000, 'price_multiplier': 0.01}}
        self.mock_strategy = MagicMock(spec=BaseStrategy)
        self.mock_strategy.weights = {'A':1, 'B':-1}
        self.train_ratio = 0.5

        # Initialize the VectorizedBacktest instance
        self.vectorized_backtest = VectorizedBacktest(
            strategy=self.mock_strategy,
            full_data=self.mock_data,
            symbols_map=self.symbols_map,
            initial_capital=10000,
            train_ratio=self.train_ratio
        )
    
    # Basic Validation
    def test_split_data(self):
        # expected
        expected_train_data = pd.DataFrame({
                'timestamp': [
                    1700161200000000000, 1700247600000000000, 1700334000000000000,
                    1700420400000000000, 1700506800000000000, 1700593200000000000,
                    1700852400000000000
                ],
                'A': [75.600, 75.300, 74.900, 74.925, 74.250, 74.425, 75.400],
                'B': [489.25, 487.00, 487.75, 489.25, 485.25, 485.50, 491.50],
        })
        expected_train_data.set_index('timestamp', inplace=True)
        
        expected_test_data = pd.DataFrame({
                'timestamp': [ 1700938800000000000, 1701025200000000000, 1701111600000000000 ],
                'A': [75.075, 75.600,  75.500],
                'B': [493.00, 493.00, 492.50],
        })
        expected_test_data.set_index('timestamp', inplace=True)

        # test
        actual_train, actual_test = self.vectorized_backtest.split_data(self.mock_data, train_ratio=0.70)
  
        # validate
        self.assertTrue(actual_train.equals(expected_train_data))
        assert_frame_equal(actual_train, expected_train_data, check_dtype=True)
        assert_frame_equal(actual_test, expected_test_data, check_dtype=True)

    def test_setup_html_content(self):
        # expected
        split_index = int(len(self.mock_data) * self.train_ratio)
        train_data = self.mock_data.iloc[:split_index]
        
        # test 
        self.vectorized_backtest.setup()
        
        # validate       
        self.mock_strategy.prepare.assert_called_once()

        # Retrieve arguments to verify details if needed
        args, _ = self.mock_strategy.prepare.call_args
        pd.testing.assert_frame_equal(args[0], train_data)
    
    def test_run_backtest_calls_generate_signals(self):
        self.vectorized_backtest._calculate_positions = MagicMock()
        self.vectorized_backtest._calculate_positions_pnl = MagicMock()
        self.vectorized_backtest._calculate_equity_curve = MagicMock()
        self.vectorized_backtest._calculate_metrics = MagicMock()
        self.vectorized_backtest.daily_data =pd.DataFrame() # mock creation becuase methodwhere  its created is mocked
        lag = 1

        # expected
        split_index = int(len(self.mock_data) * self.train_ratio)
        test_data = self.mock_data.iloc[split_index:]
        
        # test
        self.vectorized_backtest.run_backtest(lag)
        
        # validate
        self.mock_strategy.generate_signals.assert_called_once()
        self.vectorized_backtest._calculate_positions.assert_called_once()
        self.vectorized_backtest._calculate_positions_pnl.assert_called_once()
        self.vectorized_backtest._calculate_equity_curve.assert_called_once()
        self.vectorized_backtest._calculate_metrics.assert_called_once()
        args, _ = self.mock_strategy.generate_signals.call_args
        pd.testing.assert_frame_equal(args[0], test_data)

    def test_calculate_positions(self):
        signals = pd.DataFrame({
                'timestamp': [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
                ],
                'A': [None, None, -1.0, None,  0.0],
                'B': [None, None, 1.0, None,  0.0],
        })
        signals.set_index('timestamp', inplace=True)

        # expected
        data = {
            'A': [74.425, 75.400, 75.075, 75.600, 75.500],
            'B': [485.5, 491.5, 493.0, 493.0, 492.5],
            'A_position': [0.0, 0.0, 0.0, -1.0, -1.0],
            'A_position_value': [0.0, 0.0, 0.0, -30240.0, -30200.0],
            'B_position': [0.0, 0.0, 0.0, 1.0, 1.0],
            'B_position_value': [0.0, 0.0, 0.0, 24650.0, 24625.0],
        }

        # Timestamps for the index
        timestamps = [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
        ]

        # Create DataFrame with timestamp as index
        expected_df = pd.DataFrame(data, index=timestamps)
        expected_df.index.name = 'timestamp'


        # test
        self.vectorized_backtest._calculate_positions(signals, 1)

        # validate
        assert_frame_equal(self.vectorized_backtest.test_data, expected_df)
  
    def test_calculate_positions_pnl(self):
        signals = pd.DataFrame({
                'timestamp': [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
                ],
                'A': [None, None, -1.0, None,  0.0],
                'B': [None, None, 1.0, None,  0.0],
        })
        signals.set_index('timestamp', inplace=True)
        self.vectorized_backtest._calculate_positions(signals, 1)

        # expected
        data = {
            'A': [74.425, 75.400, 75.075, 75.600, 75.500],
            'B': [485.5, 491.5, 493.0, 493.0, 492.5],
            'A_position': [0.0, 0.0, 0.0, -1.0, -1.0],
            'A_position_value': [0.0, 0.0, 0.0, -30240.0, -30200.0],
            'B_position': [0.0, 0.0, 0.0, 1.0, 1.0],
            'B_position_value': [0.0, 0.0, 0.0, 24650.0, 24625.0],
            'A_position_pnl': [0.0, 0.0, 0.0, 0.0, 40.0],
            'B_position_pnl': [0.0, 0.0, 0.0, 0.0, -25.0],
            'portfolio_pnl': [0.0, 0.0, 0.0, 0.0, 15.0]
        }

        # Timestamps for the index
        timestamps = [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
        ]

        # Create DataFrame with timestamp as index
        expected_df = pd.DataFrame(data, index=timestamps)
        expected_df.index.name = 'timestamp'

        # test
        self.vectorized_backtest._calculate_positions_pnl()

        # validate
        assert_frame_equal(self.vectorized_backtest.test_data, expected_df)

    def test_calculate_equity_curve(self):
        # Set up
        signals = pd.DataFrame({
                'timestamp': [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
                ],
                'A': [None, None, -1.0, None,  0.0],
                'B': [None, None, 1.0, None,  0.0],
        })
        signals.set_index('timestamp', inplace=True)
        self.vectorized_backtest._calculate_positions(signals, 1)
        self.vectorized_backtest._calculate_positions_pnl()

        # Expected
        data = {
            'A': [74.425, 75.400, 75.075, 75.600, 75.500],
            'B': [485.5, 491.5, 493.0, 493.0, 492.5],
            'A_position': [0.0, 0.0, 0.0, -1.0, -1.0],
            'A_position_value': [0.0, 0.0, 0.0, -30240.0, -30200.0],
            'B_position': [0.0, 0.0, 0.0, 1.0, 1.0],
            'B_position_value': [0.0, 0.0, 0.0, 24650.0, 24625.0],
            'A_position_pnl': [0.0, 0.0, 0.0, 0.0, 40.0],
            'B_position_pnl': [0.0, 0.0, 0.0, 0.0, -25.0],
            'portfolio_pnl': [0.0, 0.0, 0.0, 0.0, 15.0],
            'equity_value': [10000.0,10000.0,10000.0,10000.0,10015.0 ]
        }

        # Timestamps for the index
        timestamps = [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
        ]

        # Create DataFrame with timestamp as index
        expected_df = pd.DataFrame(data, index=timestamps)
        expected_df.index.name = 'timestamp'

        # test
        self.vectorized_backtest._calculate_equity_curve()

        # validate
        assert_frame_equal(self.vectorized_backtest.test_data, expected_df, check_dtype=False, check_like=True, rtol=1e-5, atol=1e-4)

    def test_calculate_metrics(self):
      # Set up
        signals = pd.DataFrame({
                'timestamp': [
                                1700593200000000000, 1700852400000000000, 1700938800000000000, 
                                1701025200000000000, 1701111600000000000
                            ],
                'A': [None, None, -1.0, None,  0.0],
                'B': [None, None, 1.0, None,  0.0],
        })
        signals.set_index('timestamp', inplace=True)
        self.vectorized_backtest._calculate_positions(signals, 1)
        self.vectorized_backtest._calculate_positions_pnl()
        self.vectorized_backtest._calculate_equity_curve()


        # Expected
        data = {
            'A': [74.425, 75.400, 75.075, 75.600, 75.500],
            'B': [485.5, 491.5, 493.0, 493.0, 492.5],
            'A_position': [0.0, 0.0, 0.0, -1.0, -1.0],
            'A_position_value': [0.0, 0.0, 0.0, -30240.0, -30200.0],
            'B_position': [0.0, 0.0, 0.0, 1.0, 1.0],
            'B_position_value': [0.0, 0.0, 0.0, 24650.0, 24625.0],
            'A_position_pnl': [0.0, 0.0, 0.0, 0.0, 40.0],
            'B_position_pnl': [0.0, 0.0, 0.0, 0.0, -25.0],
            'portfolio_pnl': [0.0, 0.0, 0.0, 0.0, 15.0],
            'equity_value': [10000.0,10000.0,10000.0,10000.0,10015.0 ],
            'period_return': [0.0, 0.0 , 0.0, 0.0, 0.0015],
            'cumulative_return': [0.0, 0.0 , 0.0, 0.0, 0.0015],
            'drawdown': [0.0, 0.0 , 0.0, 0.0, 0.0],
        }

        # Timestamps for the index
        timestamps = [
                    1700593200000000000, 1700852400000000000, 1700938800000000000, 
                    1701025200000000000, 1701111600000000000
        ]

        # Create DataFrame with timestamp as index
        expected_df = pd.DataFrame(data, index=timestamps)
        expected_df.index.name = 'timestamp'
        
        # test
        self.vectorized_backtest._calculate_metrics()

        # validate
        assert_frame_equal(self.vectorized_backtest.test_data, expected_df, check_dtype=False, check_like=True, rtol=1e-5, atol=1e-4)
        self.assertIn("sharpe_ratio", self.vectorized_backtest.summary_stats.keys())
        self.assertTrue(self.vectorized_backtest.summary_stats['sharpe_ratio'] > 0)
        self.assertIn("annual_standard_deviation", self.vectorized_backtest.summary_stats.keys())
        self.assertTrue(self.vectorized_backtest.summary_stats['annual_standard_deviation'] > 0)

    # Type
    def test_run_backtest_with_exception_in_generate_signals(self):
        # Configure the mock to raise an exception
        self.mock_strategy.generate_signals.side_effect = Exception("Mock error")
        with self.assertRaises(Exception):
            self.vectorized_backtest.run_backtest()

    # Edge Cases
    def test_setup_with_error(self):
        # Configure the mock strategy's prepare method to raise an exception
        self.mock_strategy.prepare.side_effect = Exception("Mock preparation error")
        
        # Verify that setup raises an Exception when strategy.prepare fails
        with self.assertRaises(Exception) as context:
            self.vectorized_backtest.setup()
            
        # validate
        self.assertTrue("Mock preparation error" in str(context.exception))

if __name__ =="__main__":
    unittest.main()
