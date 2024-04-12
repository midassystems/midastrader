import unittest
import numpy as np
import pandas as pd
from contextlib import ExitStack
from ibapi.contract import Contract
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from pandas.testing import assert_frame_equal

from engine.command.parameters import Parameters
from engine.account_data import EquityDetails, Trade
from engine.events import SignalEvent, Action, ExecutionDetails
from engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent
from engine.performance.live.manager import LiveTradingSession, LivePerformanceManager
from engine.events import MarketData, BarData, QuoteData, OrderType, Action, TradeInstruction, MarketDataType


# 2024-04-10 13:13:48,126 - cointegrationzscore_logger - INFO - [{'BuyingPower': 2563178.43, 'Currency': 'USD', 'ExcessLiquidity': 768953.53, 'FullAvailableFunds': 768953.53, 'FullInitMarginReq': 263.95, 'FullMaintMarginReq': 263.95, 'FuturesPNL': -367.5, 'NetLiquidation': 769217.48, 'TotalCashBalance': -10557.9223, 'UnrealizedPnL': 0.0, 'Timestamp': '2024-04-10T13:12:24.127576'}, {'BuyingPower': 2541533.29, 'Currency': 'USD', 'ExcessLiquidity': 763767.68, 'FullAvailableFunds': 762459.99, 'FullInitMarginReq': 6802.69, 'FullMaintMarginReq': 5495.0, 'FuturesPNL': -373.3, 'NetLiquidation': 769262.67, 'TotalCashBalance': 768538.5532, 'UnrealizedPnL': -11.73, 'Timestamp': '2024-04-10T13:13:43.160076'}]
# 2024-04-10 13:13:48,126 - cointegrationzscore_logger - INFO - [{'timestamp': '2024-04-10T17:13:00+00:00', 'trade_instructions': [{'ticker': 'HE', 'order_type': 'MKT', 'action': 'SHORT', 'trade_id': 1, 'leg_id': 1, 'weight': -0.8689}, {'ticker': 'ZC', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 1, 'leg_id': 2, 'weight': 0.1311}]}, {'timestamp': '2024-04-10T17:13:05+00:00', 'trade_instructions': [{'ticker': 'HE', 'order_type': 'MKT', 'action': 'SHORT', 'trade_id': 1, 'leg_id': 1, 'weight': -0.8689}, {'ticker': 'ZC', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 1, 'leg_id': 2, 'weight': 0.1311}]}]



#TODO: edge cases
class TestLiveTradingSession(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_db_client = Mock()
        self.session = LiveTradingSession(self.mock_db_client)
        
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
        self.mock_summary_stats = [{
            "total_return": 10.0,
            "total_trades": 5,
            "total_fees": 2.5
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

        self.session.parameters = self.mock_parameters
        self.session.summary_stats = self.mock_summary_stats
        self.session.trade_data = self.mock_trades
        self.session.signal_data = self.mock_signals

    # Basic Validation
    def test_to_dict_valid(self):
        session_dict = self.session.to_dict()

        self.assertEqual(session_dict['parameters'], self.mock_parameters)
        self.assertEqual(session_dict['summary_stats'], self.mock_summary_stats)
        self.assertEqual(session_dict['signals'], self.mock_signals)
        self.assertEqual(session_dict['trades'], self.mock_trades)

    def test_save_successful(self):
        expected_return = {'id': 4, 'summary_stats': [{'ending_equity': None, 'total_fees': 0.0, 'unrealized_pnl': 0.0, 'realized_pnl': 0.0}], 'trades': [], 'signals': [], 'parameters': {'strategy_name': 'cointegrationzscore', 'tickers': ['HE', 'ZC'], 'benchmark': ['^GSPC'], 'data_type': 'BAR', 'train_start': '2020-05-18', 'train_end': '2024-01-01', 'test_start': '2024-01-02', 'test_end': '2024-01-19', 'capital': 100000.0, 'created_at': '2024-04-09T17:34:25.001994Z'}, 'price_data': []}

        with ExitStack() as stack:
            mock_create_session = stack.enter_context(patch.object(self.mock_db_client,'create_live_session', return_value = expected_return))
            mock_print = stack.enter_context(patch('builtins.print'))
            
            result = self.session.save()
            mock_create_session.assert_called_once_with(self.session.to_dict())
            self.assertEqual(expected_return, result)

    # def test_save_unsuccessful(self):
    #     response = 500
    #     with ExitStack() as stack:
    #         mock_create_session = stack.enter_context(patch.object(self.mock_db_client,'create_live_session', return_value = response))
    #         mock_print = stack.enter_context(patch('builtins.print'))
            
    #         self.session.save()
    #         mock_create_session.assert_called_once_with(self.session.to_dict())
    #         mock_print.assert_called_once_with(f"Live session save failed with response code: {response}")

    def test_save_validation_exception(self):
        def create_session_error(self):
            raise ValueError
        
        self.session.parameters = ""
        
        with ExitStack() as stack:
            mock_create_session = stack.enter_context(patch.object(self.mock_db_client,'create_live_session', side_effect = create_session_error))
            with self.assertRaisesRegex(ValueError,f"Validation Error:" ):
                self.session.save()

    def test_validate_attributes_success(self):
        try:
            self.session.validate_attributes()
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

        self.performance_manager = LivePerformanceManager(self.mock_db_client, self.mock_logger, self.mock_parameters)

        # Valid Data
        self.mock_static_stats = [{
            "total_return": 10.0,
            "total_trades": 5,
            "total_fees": 2.5
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

        # Test 
        self.performance_manager.calculate_statistics()

        # Expected Values
        expected_ending_equity = 1330.0
        expected_total_fees = 40
        
        # Validation 
        stats = self.performance_manager.summary_stats[0] 
        self.assertAlmostEqual(stats['ending_equity'], expected_ending_equity, places=2)
        self.assertAlmostEqual(stats['total_fees'], expected_total_fees, places=2)
        self.assertAlmostEqual(stats['unrealized_pnl'], 0, places=2)
        self.assertAlmostEqual(stats['realized_pnl'], 0, places=2)

    def test_create_live_session(self):
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

        self.performance_manager.calculate_statistics()

        # Test 
        self.performance_manager.create_live_session()
        live_summary = self.performance_manager.live_summary

        self.assertEqual(live_summary.parameters, self.mock_parameters.to_dict())
        self.assertEqual(live_summary.signal_data, [signal_event.to_dict()])
        self.assertEqual(live_summary.trade_data , [trade.to_dict() for trade in self.trades])

        expected_static_keys = {
                                'ending_equity', 
                                'total_fees',
                                'unrealized_pnl', 
                                'realized_pnl', 
                                }

        actual_static_keys = set(live_summary.summary_stats[0].keys())
        self.assertEqual(actual_static_keys, expected_static_keys, "Summary stats keys do not match expected keys.")


if __name__ == "__main__":
    unittest.main()