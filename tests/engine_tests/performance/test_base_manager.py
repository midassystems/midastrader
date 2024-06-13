import unittest
import numpy as np
from unittest.mock import Mock, patch
from midas.shared.orders import Action, OrderType
from midas.shared.signal import  TradeInstruction
from midas.engine.command.parameters import Parameters
from midas.shared.trade import ExecutionDetails, Trade
from midas.engine.performance import BasePerformanceManager
from midas.shared.account import Account, EquityDetails, AccountDetails
from midas.shared.market_data import MarketData, BarData, QuoteData,  MarketDataType
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, SignalEvent

class TestBasePerformanceManager(unittest.TestCase):    
    def setUp(self) -> None:
        # Mock methods
        self.mock_db_client = Mock()
        self.mock_logger = Mock()

        # Test parameters
        self.parameters = Parameters(
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
        self.performance_manager = BasePerformanceManager(self.mock_db_client, self.mock_logger, self.parameters)

        # Test data
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
        self.mock_logger.info.assert_called_once_with("\nTRADES UPDATED:\n  {'timestamp': 16555000, 'trade_id': 1, 'leg_id': 2, 'ticker': 'HEJ4', 'quantity': 10, 'avg_price': 85.98, 'trade_value': 100000, 'action': 'BUY', 'fees': 9.87}\n")

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

        # validate
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

    def test_account_log(self):
        account_info = AccountDetails(
                                full_available_funds = 100000.0, 
                                full_init_margin_req =  100000.0,
                                net_liquidation = 100000.0,
                                unrealized_pnl =  100000.0,
                                full_maint_margin_req=  100000.0,
                                currency= 'USD'
                            ) 
        
        # Test
        self.performance_manager.update_account_log(account_info)

        # Validate 
        self.assertEqual(self.performance_manager.account_log[0], account_info)
        self.mock_logger.info.assert_called_once_with(f"\nAccount Log Updated: {account_info}")

if __name__ == "__main__":
    unittest.main()