import os
import unittest
import numpy as np
import pandas as pd
from contextlib import ExitStack
from unittest.mock import Mock, patch
from pandas.testing import assert_frame_equal
from midas.shared.signal import TradeInstruction
from midas.shared.account import  EquityDetails
from midas.shared.orders import OrderType, Action
from midas.shared.trade import Trade, ExecutionDetails
from midas.engine.command.parameters import Parameters
from midas.engine.performance.backtest.manager import BacktestPerformanceManager
from midas.shared.market_data import MarketData, BarData, QuoteData, MarketDataType
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent
from midas.shared.symbol import Equity, Future, Currency, Venue, Symbol, Industry, ContractUnits

class TestPerformanceManager(unittest.TestCase):    
    def setUp(self) -> None:
        # Mock methods
        self.strategy =Mock()
        self.mock_db_client = Mock()
        self.mock_logger = Mock()

        # Test parameters object
        self.mock_parameters = Parameters(
            strategy_name="cointegrationzscore", 
            missing_values_strategy="drop",
            train_start="2021-01-01",
            train_end="2024-01-01",
            test_start="2024-01-02",
            test_end="2024-05-07",
            capital=1000000,
            data_type = MarketDataType.BAR,
            symbols = [
                        Future(ticker="HE.n.0",
                            data_ticker="HE.n.0",
                            currency=Currency.USD,  
                            exchange=Venue.CME,  
                            fees=0.85,  
                            initial_margin=5627.17,
                            quantity_multiplier=40000,
                            price_multiplier=0.01,
                            product_code="HE",
                            product_name="Lean Hogs",
                            industry=Industry.AGRICULTURE,
                            contract_size=40000,
                            contract_units=ContractUnits.POUNDS,
                            tick_size=0.00025,
                            min_price_fluctuation=10.0,
                            continuous=True,
                            lastTradeDateOrContractMonth="202404"),
                        Future(ticker="ZC.n.0",
                            data_ticker = "ZC.n.0",
                            currency=Currency.USD,
                            exchange=Venue.CBOT,
                            fees=0.85, 
                            quantity_multiplier=5000,
                            price_multiplier=0.01, 
                            initial_margin=2075.36,
                            product_code="ZC",
                            product_name="Corn",
                            industry=Industry.AGRICULTURE,
                            contract_size=5000,
                            contract_units=ContractUnits.BUSHELS,
                            tick_size=0.0025,
                            min_price_fluctuation=12.50,
                            continuous=True,
                            lastTradeDateOrContractMonth="202404")
                    ]
        )

        # Test performance manager object
        self.performance_manager = BacktestPerformanceManager(self.mock_db_client, self.mock_logger, self.mock_parameters, self.strategy,)

        # Test trade object
        self.trade_obj = Trade(
            trade_id = 1,
            leg_id = 2,
            timestamp = np.uint64(16555000),
            ticker = 'HEJ4',
            quantity = 10,
            avg_price= 85.98,
            trade_value = 100000,
            action = 'BUY',
            fees = 9.87
        )  

        # Test signal event
        self.trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=2)
        self.trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5,
                                                quantity=2)
        self.trade_instructions = [self.trade1,self.trade2]           
        self.signal_event = SignalEvent(np.uint64(1651500000), self.trade_instructions)    

        
        # Test performance data
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
        # Test
        self.performance_manager.update_trades(self.trade_obj)

        # Validate
        self.assertEqual(self.performance_manager.trades[0], self.trade_obj)
        self.mock_logger.info.assert_called_once()
    
    def test_update_trades_old_trade_valid(self):        
        self.performance_manager.trades.append(self.trade_obj)

        # Test
        self.performance_manager.update_trades(self.trade_obj)
        
        # Validate
        self.assertEqual(self.performance_manager.trades[0], self.trade_obj)
        self.assertEqual(len(self.performance_manager.trades), 1)
        self.assertFalse(self.mock_logger.info.called)
    
    def test_output_trades(self):
        # Test
        self.performance_manager.update_trades(self.trade_obj)
        
        # Validate
        self.mock_logger.info.assert_called_once_with("\nTRADES UPDATED: \n  {'timestamp': 16555000, 'trade_id': 1, 'leg_id': 2, 'ticker': 'HEJ4', 'quantity': 10, 'avg_price': 85.98, 'trade_value': 100000, 'action': 'BUY', 'fees': 9.87}\n")

    def test_update_signals_valid(self):                
        # Test
        self.performance_manager.update_signals(self.signal_event)
        
        # Validate
        self.assertEqual(self.performance_manager.signals[0], self.signal_event.to_dict())
        self.mock_logger.info.assert_called_once()
    
    def test_output_signal(self):
        # Test
        self.performance_manager.update_signals(self.signal_event)

        # Validate
        self.mock_logger.info.assert_called_once_with("\nSIGNALS UPDATED: \n  Timestamp: 1651500000 \n  Trade Instructions: \n    {'ticker': 'AAPL', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 5, 'weight': 0.5, 'quantity': 2, 'limit_price': '', 'aux_price': ''}\n    {'ticker': 'TSLA', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 6, 'weight': 0.5, 'quantity': 2, 'limit_price': '', 'aux_price': ''}\n")
    
    def test_update_equity_new_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        # Test
        self.performance_manager.update_equity(equity)
        
        # Validate
        self.assertEqual(self.performance_manager.equity_value[0], equity)
        self.mock_logger.info.assert_called_once_with("\nEQUITY UPDATED: \n  {'timestamp': 165500000, 'equity_value': 10000000.99}\n")
    
    def test_update_equity_old_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        self.performance_manager.equity_value.append(equity)

        # Test
        self.performance_manager.update_equity(equity)

        # Validate
        self.assertEqual(len(self.performance_manager.equity_value), 1)
        self.assertFalse(self.mock_logger.info.called)

    def test_aggregate_trades_valid(self):
        # Performance manager trades variable
        self.performance_manager.trades = [
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=10, avg_price=10, trade_value=-100,fees=10, action=Action.LONG.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=-10, avg_price=15, trade_value=150, fees=10,action=Action.SELL.value),
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=-10, avg_price=20, trade_value=500, fees=10, action=Action.SHORT.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=10, avg_price=18, trade_value=-180,fees=10,  action=Action.COVER.value)
        ]


        # Test
        aggregated_df = self.performance_manager._aggregate_trades()

        # Validate
        self.assertIsInstance(aggregated_df, pd.DataFrame, "Result should be a pandas DataFrame") 
        self.assertFalse(aggregated_df.empty, "Resulting DataFrame should not be empty")

        # Validate the expected columns are present
        expected_columns = ['trade_id', 'start_date', 'end_date', 'entry_value', 'exit_value', 'pnl', 'gain/loss']
        for column in expected_columns:
            self.assertIn(column, aggregated_df.columns, f"Column {column} is missing in the result")

        # Validate calculations for a specific trade_id
        trade_1 = aggregated_df[aggregated_df['trade_id'] == 1]
        self.assertEqual(trade_1.iloc[0]['entry_value'], -100)
        self.assertEqual(trade_1.iloc[0]['exit_value'], 150)
        self.assertEqual(trade_1.iloc[0]['fees'], 20)
        self.assertEqual(trade_1.iloc[0]['pnl'], 30)
        self.assertEqual(trade_1.iloc[0]['gain/loss'], 0.30,)

    def test_calculate_return_and_drawdown_valid(self):
        # Performance manager trades variable
        self.performance_manager.equity_value = [
            EquityDetails(timestamp=1640995200000000000, equity_value=1000.0),
            EquityDetails(timestamp=1641081600000000000, equity_value=1010.0),
            EquityDetails(timestamp=1641168000000000000, equity_value=1005.0),
            EquityDetails(timestamp=1641254400000000000, equity_value=1030.0),
        ]

        # Test
        df_input = pd.DataFrame(self.performance_manager.equity_value)
        df = self.performance_manager._calculate_return_and_drawdown(df_input)

        # Validate
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertFalse(df.empty) 
        
        # Validate the expected columns are present
        expected_columns = ['equity_value', 'period_return', 'cumulative_return', 'drawdown']
        for column in expected_columns:
            self.assertIn(column, df.columns, f"Column {column} is missing in the result")

        # Validate Returns
        equity_value = [1000, 1010, 1005, 1030]
        expected_daily_returns = np.diff(equity_value) / equity_value[:-1]
        expected_daily_returns =  np.insert(expected_daily_returns, 0, 0)
        self.assertAlmostEqual(df.iloc[1]['period_return'], expected_daily_returns[1])

        # Validate Cumulative Returns
        expected_cumulative_return = round((1030 - 1000) / 1000, 5)
        self.assertAlmostEqual(round(df.iloc[-1]['cumulative_return'],5), expected_cumulative_return, places=4,msg="Cumulative return calculation does not match expected value")

        # validate Drawdown
        equity_value = [1000, 1010, 1005, 1030]
        rolling_max = np.maximum.accumulate(equity_value)  # Calculate the rolling maximum
        expected_drawdowns = (equity_value - rolling_max) / rolling_max  # Calculate drawdowns in decimal format
        self.assertAlmostEqual(df['drawdown'].min(), expected_drawdowns.min(), places=4, msg="Drawdown calculation does not match expected value")

    def test_calculate_statistics(self):
        # Trades
        self.performance_manager.trades = [
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=10, avg_price=10, trade_value=-100,fees=10, action=Action.LONG.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=-10, avg_price=15, trade_value=150, fees=10,action=Action.SELL.value),
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=-10, avg_price=20, trade_value=500, fees=10, action=Action.SHORT.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=10, avg_price=18, trade_value=-180,fees=10,  action=Action.COVER.value)
        ]

        # Equity Curve
        self.performance_manager.equity_value = [
            EquityDetails(timestamp= 1641047400000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641070800000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641133800000000000, equity_value= 1030.0),
            EquityDetails(timestamp= 1641142800000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641157200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641220200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641225600000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641243600000000000, equity_value= 1330.0)
        ]

        # Test 
        self.performance_manager.calculate_statistics()

        # Validate timeseries_stats 
        expected_columns = ['equity_value', 'period_return', 'cumulative_return', 'drawdown']
        for column in expected_columns:
            self.assertIn(column, self.performance_manager.period_timeseries_stats.columns)

        for column in expected_columns:
            self.assertIn(column, self.performance_manager.daily_timeseries_stats.columns)

         # Validate that static_stats has non-null values and contains expected keys
        expected_static_keys = [
                                    'net_profit', 'total_fees', 'ending_equity', "avg_trade_profit", 
                                    'total_return','annual_standard_deviation_percentage', 'max_drawdown_percentage',
                                    "avg_win_percentage", "avg_loss_percentage","percent_profitable",
                                    'total_trades', "number_winning_trades", "number_losing_trades", "profit_and_loss_ratio", 
                                    "profit_factor", 'sortino_ratio', 'sharpe_ratio'
                                ]
            
        static_stats = self.performance_manager.static_stats[0]
        for key in expected_static_keys:
            self.assertIn(key, static_stats)
            self.assertIsNotNone(static_stats[key])

    def test_export_results(self):
        # Trades
        self.performance_manager.trades = [
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=10, avg_price=10, trade_value=-100,fees=10, action=Action.LONG.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=-10, avg_price=15, trade_value=150, fees=10,action=Action.SELL.value),
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=-10, avg_price=20, trade_value=500, fees=10, action=Action.SHORT.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=10, avg_price=18, trade_value=-180,fees=10,  action=Action.COVER.value)
        ]

        # Equity Curve
        self.performance_manager.equity_value = [
            EquityDetails(timestamp= 1641047400000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641070800000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641133800000000000, equity_value= 1030.0),
            EquityDetails(timestamp= 1641142800000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641157200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641220200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641225600000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641243600000000000, equity_value= 1330.0)
        ]

        # Signals
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=2)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5,
                                                quantity=2)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]         
        signal_event = SignalEvent(np.uint64(1717587686000000000), self.valid_trade_instructions)
        self.performance_manager.update_signals(signal_event)
        
        # Static Stats
        self.performance_manager.calculate_statistics()

        # Test 
        self.performance_manager.export_results("")
        
        # Validate file creation
        excel_file_path = os.path.join("", "output.xlsx")
        assert os.path.exists(excel_file_path), "Excel file was not created"

    
    def test_create_backtest(self):
        # Trades
        self.performance_manager.trades = [
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=10, avg_price=10, trade_value=-100,fees=10, action=Action.LONG.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=1, leg_id=1, ticker='XYZ', quantity=-10, avg_price=15, trade_value=150, fees=10,action=Action.SELL.value),
            Trade(timestamp=np.uint64(1640995200000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=-10, avg_price=20, trade_value=500, fees=10, action=Action.SHORT.value),
            Trade(timestamp=np.uint64(1641081600000000000), trade_id=2, leg_id=1, ticker='HEJ4', quantity=10, avg_price=18, trade_value=-180,fees=10,  action=Action.COVER.value)
        ]

        # Equity Curve
        self.performance_manager.equity_value = [
            EquityDetails(timestamp= 1641047400000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641070800000000000, equity_value= 1000.0),
            EquityDetails(timestamp= 1641133800000000000, equity_value= 1030.0),
            EquityDetails(timestamp= 1641142800000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641157200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641220200000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641225600000000000, equity_value= 1330.0),
            EquityDetails(timestamp= 1641243600000000000, equity_value= 1330.0)
        ]

        # Signals
        self.valid_trade1 = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=2)
        self.valid_trade2 = TradeInstruction(ticker = 'TSLA',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5,
                                                quantity=2)
        self.valid_trade_instructions = [self.valid_trade1,self.valid_trade2]
                        
        signal_event = SignalEvent(np.uint64(1717587686000000000), self.valid_trade_instructions)
        self.performance_manager.update_signals(signal_event)
        
        # Static Stats
        self.performance_manager.calculate_statistics()

        # Test 
        self.performance_manager.save()
        backtest = self.performance_manager.backtest

        # Validate
        self.assertEqual(backtest.parameters, self.mock_parameters.to_dict())
        self.assertEqual(backtest.signal_data, [signal_event.to_dict()])
        self.assertEqual(backtest.trade_data , [trade.to_dict() for trade in self.performance_manager.trades])

        # Validate static stats
        expected_static_keys = [
                    'net_profit', 'total_fees', 'ending_equity', "avg_trade_profit", 
                    'total_return','annual_standard_deviation_percentage', 'max_drawdown_percentage',
                    "avg_win_percentage", "avg_loss_percentage","percent_profitable",
                    'total_trades', "number_winning_trades", "number_losing_trades", "profit_and_loss_ratio", 
                    "profit_factor", 'sharpe_ratio','sortino_ratio'
                ]
        static_stats = list(backtest.static_stats[0].keys())

        for key in static_stats:
            self.assertIn(key, expected_static_keys)
            self.assertIsNotNone(backtest.static_stats[0][key])

        # Validate timeseries stats
        expected_timeseries_keys = {'timestamp', 'equity_value','period_return', 'cumulative_return', 'drawdown'} 
        actual_daily_timeseries_keys = set(backtest.daily_timeseries_stats[0].keys())
        actual_period_timeseries_keys = set(backtest.period_timeseries_stats[0].keys())
        
        self.assertEqual(actual_daily_timeseries_keys, expected_timeseries_keys, "Timeseries stats keys do not match expected keys.")
        self.assertEqual(actual_period_timeseries_keys, expected_timeseries_keys, "Timeseries stats keys do not match expected keys.")


if __name__ == "__main__":
    unittest.main()