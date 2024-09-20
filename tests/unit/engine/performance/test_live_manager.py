import unittest
import numpy as np
import pandas as pd
from contextlib import ExitStack
from ibapi.contract import Contract
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from pandas.testing import assert_frame_equal
from midas.shared.signal import TradeInstruction
from midas.shared.orders import Action, OrderType
from midas.shared.trade import Trade
from midas.engine.command.parameters import Parameters
from midas.shared.account import EquityDetails, Account
from midas.engine.performance.live.manager import LivePerformanceManager
from midas.shared.market_data import MarketData, BarData, QuoteData, MarketDataType
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent

class TestPerformanceManager(unittest.TestCase):    
    def setUp(self) -> None:
        # Mock methods
        self.mock_db_client = Mock()
        self.mock_logger = Mock()

        # Test parameter object
        self.mock_parameters = Parameters(
            strategy_name="cointegrationzscore", 
            capital= 100000, 
            data_type= MarketDataType.BAR, 
            train_start= "2018-05-18", 
            train_end= "2023-01-18", 
            test_start= "2023-01-19", 
            test_end= "2024-01-19", 
            tickers= ["HE.n.0", "ZC.n.0"], 
        )

        # Performance manager instance
        self.performance_manager = LivePerformanceManager(self.mock_db_client, self.mock_logger, self.mock_parameters)

        # Test signal event
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
                        
        self.signal_event = SignalEvent(np.uint64(1651500000), self.valid_trade_instructions)

        # Valid performance data
        self.mock_static_stats = [{
            "total_return": 10.0,
            "total_trades": 5,
            "total_fees": 2.5
        }]
        self.mock_trades =  Trade(
            timestamp= np.uint(16500000000), 
            ticker= "AAPL",
            trade_id= 1,
            leg_id = 0,
            quantity= 1,
            avg_price= 99.99,
            trade_value= 99.99,
            trade_cost=99.99,
            action="BUY",
            fees=0.0 
        )
        
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
        trade_id = 12345
        
        # Test
        self.performance_manager.update_trades(trade_id, self.mock_trades)

        # Validate
        self.assertEqual(self.performance_manager.trades[trade_id], self.mock_trades)
        self.mock_logger.info.assert_called_once()
    
    def test_update_trades_old_trade_valid(self):  
        trade_id = 12345
        self.performance_manager.update_trades(trade_id, self.mock_trades)   

        # Test
        self.mock_trades.action = "SELL"   
        self.performance_manager.update_trades(trade_id, self.mock_trades)   
        
        # Validate
        self.assertEqual(self.performance_manager.trades[trade_id], self.mock_trades)
        self.assertEqual(self.performance_manager.trades[trade_id].action, "SELL")
        self.assertEqual(len(self.performance_manager.trades), 1)
        self.mock_logger.info.assert_called
    
    def test_output_trades(self):
        trade_id = 12345

        # Test
        self.performance_manager.update_trades(trade_id, self.mock_trades)   

        # Validate
        self.mock_logger.info.assert_called_once_with('\nTrade Updated:\n  Timestamp: 16500000000\n  Trade ID: 1\n  Leg ID: 0\n  Ticker: AAPL\n  Quantity: 1\n  Avg Price: 99.99\n  Trade Value: 99.99\n  Trade Cost: 99.99\n  Action: BUY\n  Fees: 0.0\n\n')

    def test_update_trade_commission(self):
        trade_id = 12345
        self.performance_manager.update_trades(trade_id, self.mock_trades)   

        # Test 
        self.performance_manager.update_trade_commission(trade_id, 2.97)

        # Validate
        self.mock_logger.info.assert_called
        self.assertEqual(self.performance_manager.trades[trade_id].fees, 2.97)
    
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
        equity = EquityDetails(timestamp= 165500000, equity_value = 10000000.99)

        # Test
        self.performance_manager.update_equity(equity)

        # Validate
        self.assertEqual(self.performance_manager.equity_value[0], equity)
        self.mock_logger.info.assert_called_once_with("\nEQUITY UPDATED: \n  {'timestamp': 165500000, 'equity_value': 10000000.99}\n")
    
    def test_update_equity_old_valid(self):
        equity = EquityDetails(timestamp= 165500000, equity_value = 10000000.99)
        self.performance_manager.equity_value.append(equity)

        # Test
        self.performance_manager.update_equity(equity)
        
        # Validate
        self.assertEqual(len(self.performance_manager.equity_value), 1)
        self.assertFalse(self.mock_logger.info.called)
        
    def test_create_live_session(self):
        # Signals
        self.performance_manager.update_signals(self.signal_event)

        # Trades
        trades = {123: {"timestamp": "2024-01-01", "ticker": "AAPL", "quantity": "1.000","cumQty": "1.00","price": 99.99,"AvPrice": 99.99,"action": "BUY","cost":0,"currency": "USD"},
                  1234: {"timestamp": "2024-01-01", "ticker": "AAPL", "quantity": "1.000","cumQty": "1.00","price": 99.99,"AvPrice": 99.99,"action": "BUY","cost":0,"currency": "USD"},
                  12345: {"timestamp": "2024-01-01", "ticker": "AAPL", "quantity": "1.000","cumQty": "1.00","price": 99.99,"AvPrice": 99.99,"action": "BUY","cost":0,"currency": "USD"}}
        self.performance_manager.trades = trades

        # Account
        self.performance_manager.account_log = [
            Account(
                buying_power= 2563178.43, 
                currency= 'USD', 
                excess_liquidity= 768953.53, 
                full_available_funds= 768953.53, 
                full_init_margin_req= 263.95, 
                full_maint_margin_req= 263.95, 
                futures_pnl= -367.5, 
                net_liquidation= 769217.48, 
                total_cash_balance= -10557.9223, 
                unrealized_pnl= 0.0, 
                timestamp= np.uint64(165000000000)
            ),
            Account(
                buying_power= 2541533.29, 
                currency= 'USD', 
                excess_liquidity= 763767.68, 
                full_available_funds= 762459.99, 
                full_init_margin_req= 6802.69, 
                full_maint_margin_req= 5495.0, 
                futures_pnl= -373.3, 
                net_liquidation= 769262.67, 
                total_cash_balance= 768538.5532, 
                unrealized_pnl= -11.73, 
                timestamp= np.uint64(166000000000)
            )
        ]

        # Test 
        self.performance_manager.save()
        live_summary = self.performance_manager.live_summary
        
        # Validate
        self.assertEqual(live_summary.parameters, self.mock_parameters.to_dict())
        self.assertEqual(live_summary.signal_data, [self.signal_event.to_dict()])
        self.assertEqual(live_summary.trade_data ,  list(trades.values()))

        # Validate account
        expected_account = [
            {
                'start_timestamp': 165000000000, 
                'start_full_available_funds': 768953.53, 
                'start_full_init_margin_req': 263.95, 
                'start_net_liquidation': 769217.48, 
                'start_buying_power': 2563178.43, 
                'start_unrealized_pnl': 0.00, 
                'start_full_maint_margin_req': 263.95, 
                'start_excess_liquidity': 768953.53, 
                'start_futures_pnl': -367.50, 
                'start_total_cash_balance': -10557.9223, 
                'end_timestamp': 166000000000,
                'end_full_available_funds': 762459.99, 
                'end_full_init_margin_req': 6802.69, 
                'end_net_liquidation': 769262.67, 
                'end_unrealized_pnl': -11.73, 
                'end_full_maint_margin_req': 5495.00, 
                'end_excess_liquidity': 763767.68, 
                'end_buying_power': 2541533.29, 
                'end_futures_pnl': -373.30, 
                'end_total_cash_balance': 768538.5532, 
                'currency': 'USD', 
            }
        ]
        self.assertEqual(live_summary.account_data, expected_account)


if __name__ == "__main__":
    unittest.main()
