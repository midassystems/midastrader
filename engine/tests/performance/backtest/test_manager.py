import unittest
from unittest.mock import Mock, patch
from contextlib import ExitStack
from ibapi.contract import Contract
from datetime import datetime, timezone
from pandas.testing import assert_frame_equal
import pandas as pd
import numpy as np

from midas.performance.backtest.manager import Backtest, BacktestPerformanceManager
from midas.performance.regression import RegressionAnalysis
from midas.account_data import EquityDetails, Trade
from midas.events import SignalEvent, Action, ExecutionDetails
from midas.command.parameters import Parameters
from midas.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent
from midas.events import MarketData, BarData, QuoteData, OrderType, Action, TradeInstruction, MarketDataType

#TODO: edge cases
class TestBacktest(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_db_client = Mock()
        self.backtest = Backtest(self.mock_db_client)
        self.mock_parameters = {
            "strategy_name": "cointegrationzscore", 
            "capital": 100000, 
            "data_type": "BAR", 
            "strategy_allocation": 1.0, 
            "train_start": "2018-05-18", 
            "train_end": "2023-01-19", 
            "test_start": "2023-01-19", 
            "test_end": "2024-01-19", 
            "tickers": ["HE.n.0", "ZC.n.0"], 
            "benchmark": ["^GSPC"]
        }
        self.mock_static_stats = [{
            "total_return": 10.0,
            "total_trades": 5,
            "total_fees": 2.5
        }]
        self.mock_timeseries_stats =  [{
            "timestamp": "2023-12-09T12:00:00Z",
            "equity_value": 10000.0,
            "percent_drawdown": 9.9, 
            "cumulative_return": -0.09, 
            "daily_return": 79.9
        }]
        self.mock_trades =  [{
            "trade_id": 1, 
            "leg_id": 1, 
            "timestamp": "2023-01-03T00:00:00+0000", 
            "symbol": "AAPL", 
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

        self.backtest.parameters = self.mock_parameters
        self.backtest.static_stats = self.mock_static_stats
        self.backtest.timeseries_stats = self.mock_timeseries_stats
        self.backtest.trade_data = self.mock_trades
        self.backtest.signal_data = self.mock_signals

    # Basic Validation
    def test_to_dict_valid(self):
        backtest_dict = self.backtest.to_dict()

        self.assertEqual(backtest_dict['parameters'], self.mock_parameters)
        self.assertEqual(backtest_dict['static_stats'], self.mock_static_stats)
        self.assertEqual(backtest_dict['timeseries_stats'], self.mock_timeseries_stats)
        self.assertEqual(backtest_dict['signals'], self.mock_signals)
        self.assertEqual(backtest_dict['trades'], self.mock_trades)

    def test_save_successful(self):
        with ExitStack() as stack:
            mock_create_backtest = stack.enter_context(patch.object(self.mock_db_client,'create_backtest', return_value = 201))
            mock_print = stack.enter_context(patch('builtins.print'))
            
            self.backtest.save()
            mock_create_backtest.assert_called_once_with(self.backtest.to_dict())
            mock_print.assert_called_once_with("Backtest save successful.")

    def test_save_unsuccessful(self):
        response = 500
        with ExitStack() as stack:
            mock_create_backtest = stack.enter_context(patch.object(self.mock_db_client,'create_backtest', return_value = response))
            mock_print = stack.enter_context(patch('builtins.print'))
            
            self.backtest.save()
            mock_create_backtest.assert_called_once_with(self.backtest.to_dict())
            mock_print.assert_called_once_with(f"Backtest save failed with response code: {response}")

    def test_save_validation_exception(self):
        def create_backtest_error(self):
            raise ValueError
        
        self.backtest.parameters = ""
        
        with ExitStack() as stack:
            mock_create_backtest = stack.enter_context(patch.object(self.mock_db_client,'create_backtest', side_effect = create_backtest_error))
            with self.assertRaisesRegex(ValueError,f"Validation Error:" ):
                self.backtest.save()

    def test_validate_attributes_success(self):
        try:
            self.backtest.validate_attributes()
        except ValueError:
            self.fail("validate_attributes() raised ValueError unexpectedly!")

class TestPerformanceManager(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_db_client = Mock()
        self.mock_logger = Mock()
        self.mock_parameters = Parameters(
            strategy_name="cointegrationzscore", 
            capital= 100000, 
            data_type= MarketDataType.BAR, 
            train_start= "2018-05-18", 
            train_end= "2023-01-18", 
            test_start= "2023-01-19", 
            test_end= "2024-01-19", 
            tickers= ["HE.n.0", "ZC.n.0"], 
            benchmark= ["^GSPC"]
        )

        self.performance_manager = BacktestPerformanceManager(self.mock_db_client, self.mock_logger, self.mock_parameters)

        # Valid Data
        self.mock_static_stats = [{
            "total_return": 10.0,
            "total_trades": 5,
            "total_fees": 2.5
        }]
        self.mock_timeseries_stats =  [{
            "timestamp": "2023-12-09T12:00:00Z",
            "equity_value": 10000.0,
            "percent_drawdown": 9.9, 
            "cumulative_return": -0.09, 
            "daily_return": 79.9
        }]
        self.mock_trades =  [{
            "trade_id": 1, 
            "leg_id": 1, 
            "timestamp": "2023-01-03T00:00:00+0000", 
            "symbol": "AAPL", 
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

    # Basic Validation
    def test_update_trades_new_trade_valid(self): 
        trade = Trade(
                timestamp= 165000000,
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        )       

        self.performance_manager.update_trades(trade)
        self.assertEqual(self.performance_manager.trades[0], trade.to_dict())
        self.mock_logger.info.assert_called_once()
    
    def test_update_trades_old_trade_valid(self):        
        trade = Trade(
                timestamp= 165000000,
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        )  
        self.performance_manager.trades.append(trade.to_dict())

        self.performance_manager.update_trades(trade)
        self.assertEqual(self.performance_manager.trades[0], trade.to_dict())
        self.assertEqual(len(self.performance_manager.trades), 1)
        self.assertFalse(self.mock_logger.info.called)
    
    def test_output_trades(self):
        trade = Trade(
                timestamp= 165000000,
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        ) 
        self.performance_manager.update_trades(trade)
        self.mock_logger.info.assert_called_once_with("\nTrades Updated: \n {'timestamp': '1975-03-25T17:20:00+00:00', 'trade_id': 2, 'leg_id': 2, 'ticker': 'HEJ4', 'quantity': -10, 'price': 50, 'cost': -500, 'action': 'SHORT', 'fees': 70} \n")

    def test_update_signals_valid(self):        
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]
                        
        signal_event = SignalEvent(1651500000, 10000,self.valid_trade_instructions)

        self.performance_manager.update_signals(signal_event)
        self.assertEqual(self.performance_manager.signals[0], signal_event.to_dict())
        self.mock_logger.info.assert_called_once()
    
    def test_output_signal(self):
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]
                        
        signal_event = SignalEvent(1651500000, 10000,self.valid_trade_instructions)
        
        self.performance_manager.update_signals(signal_event)
        self.mock_logger.info.assert_called_once_with("\nSignals Updated:  {'timestamp': '2022-05-02T14:00:00+00:00', 'trade_instructions': [{'ticker': 'AAPL', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 5, 'weight': 0.5}, {'ticker': 'TSLA', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 6, 'weight': 0.5}]} \n")

    def test_update_equity_new_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        
        self.performance_manager.update_equity(equity)

        self.assertEqual(self.performance_manager.equity_value[0], equity)
        self.mock_logger.info.assert_called_once_with((f"\nEquity Updated: {equity}"))
    
    def test_update_equity_old_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        self.performance_manager.equity_value.append(equity)

        self.performance_manager.update_equity(equity)
        self.assertEqual(len(self.performance_manager.equity_value), 1)
        self.assertFalse(self.mock_logger.info.called)

    def test_aggregate_trades_valid(self):
        # Adjusted trades data to use ExecutionDetails format
        self.performance_manager.trades = [
            ExecutionDetails(timestamp='2022-01-01', trade_id=1, leg_id=1, symbol='XYZ', quantity=10, price=10, cost=-100,fees=10, action=Action.LONG.value),
            ExecutionDetails(timestamp='2022-01-02', trade_id=1, leg_id=1, symbol='XYZ', quantity=-10, price=15, cost=150, fees=10,action=Action.SELL.value),
            ExecutionDetails(timestamp='2022-01-01', trade_id=2, leg_id=1, symbol='HEJ4', quantity=-10, price=20, cost=500, fees=10,action=Action.SHORT.value),
            ExecutionDetails(timestamp='2022-01-02', trade_id=2, leg_id=1, symbol='HEJ4', quantity=10, price=18, cost=-180, fees=10,  action=Action.COVER.value)
        ]

        # Call the method
        aggregated_df = self.performance_manager._aggregate_trades()

        # Check if the result is a DataFrame
        self.assertIsInstance(aggregated_df, pd.DataFrame, "Result should be a pandas DataFrame")
        
        # Check if the DataFrame is not empty
        self.assertFalse(aggregated_df.empty, "Resulting DataFrame should not be empty")

        # Validate the expected columns are present
        expected_columns = ['trade_id', 'start_date', 'end_date', 'entry_value', 'exit_value', 'pnl', 'gain/loss']
        for column in expected_columns:
            self.assertIn(column, aggregated_df.columns, f"Column {column} is missing in the result")

        # Validate calculations for a specific trade_id
        trade_1 = aggregated_df[aggregated_df['trade_id'] == 1]
        self.assertEqual(trade_1.iloc[0]['entry_value'], -100, "Incorrect entry value for trade_id 1")
        self.assertEqual(trade_1.iloc[0]['exit_value'], 150, "Incorrect exit value for trade_id 1")
        self.assertEqual(trade_1.iloc[0]['fees'], 20, "Incorrect fees for trade_id 1")
        self.assertEqual(trade_1.iloc[0]['pnl'], 30, "Incorrect net pnl for trade_id 1")
        self.assertEqual(trade_1.iloc[0]['gain/loss'], 0.30, "Incorrect gain/loss for trade_id 1")

    def test_standardize_to_granularity(self):
        self.equity_curve = [
            EquityDetails(timestamp='2022-01-01', equity_value=1000.0),
            EquityDetails(timestamp='2022-01-02', equity_value=99),
            EquityDetails(timestamp='2022-01-02', equity_value=1010.0),
            EquityDetails(timestamp='2022-01-03', equity_value=1005.0)
        ]
        
        # Expected Data
        data = {
                'timestamp': ['2022-01-01', '2022-01-02', '2022-01-03'],
                'equity_value': [1000.0, 1010.0, 1005.0],
            }
        expected_df = pd.DataFrame(data)
        expected_df['timestamp'] = pd.to_datetime(expected_df['timestamp'])
        expected_df.set_index('timestamp', inplace=True)
        expected_df = expected_df.asfreq('D')

        # Test 
        df_input = pd.DataFrame(self.equity_curve)
        df = self.performance_manager._standardize_to_granularity(df_input, 'equity_value')
        
        # Validate
        # Validate the output types
        self.assertIsInstance(df, pd.DataFrame, "Equity values should be a dataframe.")
        
        # Validate the values are the last of each day
        assert_frame_equal(df, expected_df)

    def test_standardize_to_granularity_intraday_valid(self):
        self.equity_curve = [
            EquityDetails(timestamp= '2022-01-01 09:30', equity_value= 1000.0),
            EquityDetails(timestamp ='2022-01-01 16:00', equity_value= 1005.0),
            EquityDetails(timestamp= '2022-01-02 09:30', equity_value= 1010.0),
            EquityDetails(timestamp= '2022-01-02 12:00', equity_value= 1012.0),
            EquityDetails(timestamp= '2022-01-02 16:00', equity_value= 1015.0),
            EquityDetails(timestamp= '2022-01-03 09:30', equity_value= 1005.0),
            EquityDetails(timestamp= '2022-01-03 11:00', equity_value= 1007.0),
            EquityDetails(timestamp= '2022-01-03 16:00', equity_value= 1010.0)
        ]
        
        # Expected Data
        data = {
                'timestamp': ['2022-01-01', '2022-01-02', '2022-01-03'],
                'equity_value': [1005.0, 1015.0, 1010.0],
            }
        expected_df = pd.DataFrame(data)
        expected_df['timestamp'] = pd.to_datetime(expected_df['timestamp'])
        expected_df.set_index('timestamp', inplace=True)
        expected_df = expected_df.asfreq('D')

        # Test 
        df_input = pd.DataFrame(self.equity_curve)
        df = self.performance_manager._standardize_to_granularity(df_input, 'equity_value')
        
        # Validate
        # Validate the output types
        self.assertIsInstance(df, pd.DataFrame, "Equity values should be a dataframe.")
        
        # Validate the values are the last of each day
        assert_frame_equal(df, expected_df)

    def test_calculate_return_and_drawdown_valid(self):
        self.performance_manager.equity_value = [
            EquityDetails(timestamp='2022-01-01', equity_value=1000.0),
            EquityDetails(timestamp='2022-01-02', equity_value=1010.0),
            EquityDetails(timestamp='2022-01-03', equity_value=1005.0),
            EquityDetails(timestamp='2022-01-04', equity_value=1030.0),
        ]

        df_input = pd.DataFrame(self.performance_manager.equity_value)
        df = self.performance_manager._calculate_return_and_drawdown(df_input)

        # Check if the result is a DataFrame
        self.assertTrue(isinstance(df, pd.DataFrame), "Result should be a pandas DataFrame")
        
        # Check if the DataFrame is not empty
        self.assertFalse(df.empty, "Resulting DataFrame should not be empty")

        # Validate the expected columns are present
        expected_columns = ['equity_value', 'period_return', 'cumulative_return', 'drawdown']
        for column in expected_columns:
            self.assertIn(column, df.columns, f"Column {column} is missing in the result")

        # Validate Daily Returns
        equity_value = [1000, 1010, 1005, 1030]
        expected_daily_returns = np.diff(equity_value) / equity_value[:-1]
        expected_daily_returns =  np.insert(expected_daily_returns, 0, 0)
        
        self.assertAlmostEqual(df.iloc[1]['period_return'], expected_daily_returns[1])
        

        # Validat Cumulative Returns
        expected_cumulative_return = round((1030 - 1000) / 1000, 5)
        self.assertAlmostEqual(round(df.iloc[-1]['cumulative_return'],5), expected_cumulative_return, places=4,msg="Cumulative return calculation does not match expected value")

        # Test Drawdown
        equity_value = [1000, 1010, 1005, 1030]
        rolling_max = np.maximum.accumulate(equity_value)  # Calculate the rolling maximum
        expected_drawdowns = (equity_value - rolling_max) / rolling_max  # Calculate drawdowns in decimal format
        self.assertAlmostEqual(df['drawdown'].min(), expected_drawdowns.min(), places=4, msg="Drawdown calculation does not match expected value")

    def test_calculate_statistics(self):
        # Trades
        self.performance_manager.trades = [
            ExecutionDetails(timestamp='2022-01-01', trade_id=1, leg_id=1, symbol='XYZ', quantity=10, price=10, cost=-100,fees=10, action=Action.LONG.value),
            ExecutionDetails(timestamp='2022-01-02', trade_id=1, leg_id=1, symbol='XYZ', quantity=-10, price=15, cost=150, fees=10,action=Action.SELL.value),
            ExecutionDetails(timestamp='2022-01-01', trade_id=2, leg_id=1, symbol='HEJ4', quantity=-10, price=20, cost=500, fees=10,action=Action.SHORT.value),
            ExecutionDetails(timestamp='2022-01-02', trade_id=2, leg_id=1, symbol='HEJ4', quantity=10, price=18, cost=-180, fees=10,  action=Action.COVER.value)
        ]

        # Equity Curve
        self.performance_manager.equity_value = [
            EquityDetails(timestamp='2022-01-01 09:30', equity_value=1000.0),  # Initial equity
            EquityDetails(timestamp='2022-01-01 16:00', equity_value=1000.0),  # No change, trades open
            EquityDetails(timestamp='2022-01-02 09:30', equity_value=1030.0),  # Reflecting Trade 1 PnL
            EquityDetails(timestamp='2022-01-02 12:00', equity_value=1330.0),  # Reflecting Trade 2 PnL
            EquityDetails(timestamp='2022-01-02 16:00', equity_value=1330.0),  # No additional trades
            EquityDetails(timestamp='2022-01-03 09:30', equity_value=1330.0),  # Assuming no further trades
            EquityDetails(timestamp='2022-01-03 11:00', equity_value=1330.0),
            EquityDetails(timestamp='2022-01-03 16:00', equity_value=1330.0)
        ]


        # Benchmark Curve
        self.mock_benchmark_data = [
            {'timestamp': '2022-01-01', 'close': 2000.0},
            {'timestamp': '2022-01-02', 'close': 2010.0},
            {'timestamp': '2022-01-03', 'close': 2030.0},
        ]

        # Mock the get_benchmark_data method to return the mock benchmark data
        self.mock_db_client.get_benchmark_data.return_value = self.mock_benchmark_data
        # regresson_analysis = RegressionAnalysis(self.performance_manager.equity_value, self.mock_benchmark_data )


        # Test 
        self.performance_manager.calculate_statistics()

        # Validation
        # timeseries_stats 
        expected_columns = ['equity_value', 'period_return', 'cumulative_return', 'drawdown','daily_strategy_return', 'daily_benchmark_return']
        for column in expected_columns:
            self.assertIn(column, self.performance_manager.timeseries_stats.columns)

        # self.assertFalse(self.performance_manager.timeseries_stats[expected_columns].isnull().values.any())

         # Validate that static_stats has non-null values and contains expected keys
        expected_static_keys = ['net_profit', 'total_fees', 'total_return', 'ending_equity', 'max_drawdown', 'total_trades',"num_winning_trades", 
                                "num_lossing_trades", "avg_win_percent", "avg_loss_percent", "percent_profitable", "profit_and_loss", "profit_factor", 
                                "avg_trade_profit", 'sortino_ratio']
            
        static_stats = self.performance_manager.static_stats[0]
        for key in expected_static_keys:
            self.assertIn(key, static_stats)
            self.assertIsNotNone(static_stats[key])

        # Validate that regression_stats has non-null values and contains expected keys
        expected_regression_keys = ["r_squared", "p_value_alpha", "p_value_beta", "risk_free_rate", "alpha", 
                                    "beta", "sharpe_ratio", "annualized_return", "market_contribution", "idiosyncratic_contribution", 
                                    "total_contribution", "annualized_volatility", "market_volatility", "idiosyncratic_volatility", 
                                    "total_volatility", "portfolio_dollar_beta", "market_hedge_nmv"]
        
        regression_stats = self.performance_manager.regression_stats[0]
        for key in expected_regression_keys:
            self.assertIn(key, regression_stats)
            self.assertIsNotNone(regression_stats[key])

    def test_create_backtest(self):
        # Signals
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]
                        
        signal_event = SignalEvent(1651500000, 10000,self.valid_trade_instructions)

        self.performance_manager.update_signals(signal_event)

        # Trades
        self.trades = [
            Trade(timestamp=1640995200, trade_id=1, leg_id=1, ticker='XYZ', quantity=10, price=10, cost=-100,fees=10, action=Action.LONG.value),
            Trade(timestamp=1641081600, trade_id=1, leg_id=1, ticker='XYZ', quantity=-10, price=15, cost=150, fees=10,action=Action.SELL.value),
            Trade(timestamp=1640995200, trade_id=2, leg_id=1, ticker='HEJ4', quantity=-10, price=20, cost=500, fees=10,action=Action.SHORT.value),
            Trade(timestamp=1641081600, trade_id=2, leg_id=1, ticker='HEJ4', quantity=10, price=18, cost=-180, fees=10,  action=Action.COVER.value)
        ]

        for trade in self.trades:
            self.performance_manager.update_trades(trade)

        # Equity Curve
        self.performance_manager.equity_value = [
            EquityDetails(timestamp='2022-01-01 09:30', equity_value=1000.0),  # Initial equity
            EquityDetails(timestamp='2022-01-01 16:00', equity_value=1000.0),  # No change, trades open
            EquityDetails(timestamp='2022-01-02 09:30', equity_value=1030.0),  # Reflecting Trade 1 PnL
            EquityDetails(timestamp='2022-01-02 12:00', equity_value=1330.0),  # Reflecting Trade 2 PnL
            EquityDetails(timestamp='2022-01-02 16:00', equity_value=1330.0),  # No additional trades
            EquityDetails(timestamp='2022-01-03 09:30', equity_value=1330.0),  # Assuming no further trades
            EquityDetails(timestamp='2022-01-03 11:00', equity_value=1330.0),
            EquityDetails(timestamp='2022-01-03 16:00', equity_value=1330.0)
        ]


        # Benchmark Curve
        self.mock_benchmark_data = [
            {'timestamp': '2022-01-01', 'close': 2000.0},
            {'timestamp': '2022-01-02', 'close': 2010.0},
            {'timestamp': '2022-01-03', 'close': 2030.0},
        ]

        # Mock the get_benchmark_data method to return the mock benchmark data
        self.mock_db_client.get_benchmark_data.return_value = self.mock_benchmark_data
        self.performance_manager.calculate_statistics()

        # Test 
        self.performance_manager.create_backtest()
        backtest = self.performance_manager.backtest

        self.assertEqual(backtest.parameters, self.mock_parameters.to_dict())
        self.assertEqual(backtest.signal_data, [signal_event.to_dict()])
        self.assertEqual(backtest.trade_data , [trade.to_dict() for trade in self.trades])

        expected_static_keys = {
                                'net_profit', 
                                'total_return', 
                                'max_drawdown', 
                                # 'annual_standard_deviation', 
                                'ending_equity', 
                                'total_fees',
                                'total_trades', 
                                'num_winning_trades', 
                                'num_lossing_trades',
                                'avg_win_percent', 
                                'avg_loss_percent', 
                                'percent_profitable', 
                                'profit_and_loss', 
                                'profit_factor', 
                                'avg_trade_profit',
                                'sortino_ratio', 
        }
        actual_static_keys = set(backtest.static_stats[0].keys())
        self.assertEqual(actual_static_keys, expected_static_keys, "Static stats keys do not match expected keys.")

        expected_reg_keys = {"r_squared", "p_value_alpha", "p_value_beta", "risk_free_rate", "alpha", "beta", "sharpe_ratio", 
                            "annualized_return", "market_contribution", "idiosyncratic_contribution", 
                            "total_contribution", "annualized_volatility", "market_volatility", 
                            "idiosyncratic_volatility", "total_volatility", "portfolio_dollar_beta", "market_hedge_nmv"}

        actual_reg_keys = set(backtest.regression_stats[0].keys())
        self.assertEqual(actual_reg_keys, expected_reg_keys, "Regression stats keys do not match expected keys.")

        expected_timeseries_keys = {'timestamp', 'equity_value','period_return', 'cumulative_return', 'drawdown', 'daily_strategy_return', 'daily_benchmark_return'}  # Adjust based on your actual expected output
        actual_timeseries_keys = set(backtest.timeseries_stats[0].keys())
        self.assertEqual(actual_timeseries_keys, expected_timeseries_keys, "Timeseries stats keys do not match expected keys.")


if __name__ == "__main__":
    unittest.main()