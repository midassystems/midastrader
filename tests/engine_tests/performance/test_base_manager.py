import unittest
import numpy as np
import pandas as pd
from contextlib import ExitStack
from unittest.mock import Mock, patch

from midas.engine.command.parameters import Parameters
from midas.engine.performance import BasePerformanceManager
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, SignalEvent

from midas.shared.orders import Action, OrderType
from midas.shared.signal import  TradeInstruction
from midas.shared.trade import ExecutionDetails, Trade
from midas.shared.portfolio import AccountDetails, EquityDetails
from midas.shared.market_data import MarketData, BarData, QuoteData,  MarketDataType

#TODO: edge cases
class TestBasePerformanceManager(unittest.TestCase):    
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
        )

        self.performance_manager = BasePerformanceManager(self.mock_db_client, self.mock_logger, self.mock_parameters)

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
                timestamp= np.uint64(165000000),
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        )       
        # test
        self.performance_manager.update_trades(trade)

        # validate
        self.assertEqual(self.performance_manager.trades[0], trade)
        self.mock_logger.info.assert_called_once()
    
    def test_update_trades_old_trade_valid(self):        
        trade = Trade(
                timestamp= np.uint64(165000000),
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        )  
        self.performance_manager.trades.append(trade)
        
        # test
        self.performance_manager.update_trades(trade)

        # validate
        self.assertEqual(self.performance_manager.trades[0], trade)
        self.assertEqual(len(self.performance_manager.trades), 1)
        self.assertFalse(self.mock_logger.info.called)
    
    def test_output_trades(self):
        trade = Trade(
                timestamp= np.uint64(165000000000000000),
                trade_id= 2,
                leg_id=2,
                ticker = 'HEJ4',
                quantity= round(-10,4),
                price= 50,
                cost= round(50 * -10, 2),
                action=  Action.SHORT.value,
                fees= 70 # because not actually a trade
        ) 
        # test
        self.performance_manager.update_trades(trade)

        # validate
        self.mock_logger.info.assert_called_once_with('\nTrades Updated:\n  Timestamp: 1975-03-25T17:20:00+00:00\n  Trade ID: 2\n  Leg ID: 2\n  Ticker: HEJ4\n  Quantity: -10\n  Price: 50\n  Cost: -500\n  Action: SHORT\n  Fees: 70\n')

    def test_update_signals_valid(self):        
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
                        
        signal_event = SignalEvent(np.uint64(1651500000), self.valid_trade_instructions)
        
        # test
        self.performance_manager.update_signals(signal_event)
        
        # validate
        self.assertEqual(self.performance_manager.signals[0], signal_event.to_dict())
        self.mock_logger.info.assert_called_once()
    
    def test_output_signal(self):
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
                        
        signal_event = SignalEvent(np.uint64(1651500000), self.valid_trade_instructions)
        
        # test
        self.performance_manager.update_signals(signal_event)

        # validate
        self.mock_logger.info.assert_called_once_with("\nSignals Updated:  {'timestamp': 1651500000, 'trade_instructions': [{'ticker': 'AAPL', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 5, 'weight': 0.5, 'quantity': 2}, {'ticker': 'TSLA', 'order_type': 'MKT', 'action': 'LONG', 'trade_id': 2, 'leg_id': 6, 'weight': 0.5, 'quantity': 2}]} \n")

    def test_update_equity_new_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        
        # test
        self.performance_manager.update_equity(equity)

        # validate
        self.assertEqual(self.performance_manager.equity_value[0], equity)
        self.mock_logger.info.assert_called_once_with((f"\nEquity Updated: {equity}"))
    
    def test_update_equity_old_valid(self):
        equity = EquityDetails(
                    timestamp= 165500000,
                    equity_value = 10000000.99
                )
        self.performance_manager.equity_value.append(equity)
        
        # test
        self.performance_manager.update_equity(equity)

        # validate
        self.assertEqual(len(self.performance_manager.equity_value), 1)
        self.assertFalse(self.mock_logger.info.called)

    def test_account_log(self):
        valid_account_info = AccountDetails(FullAvailableFunds = 100000.0, 
                            FullInitMarginReq =  100000.0,
                            NetLiquidation = 100000.0,
                            UnrealizedPnL =  100000.0,
                            FullMaintMarginReq =  100000.0,
                            Currency = 'USD') 
        
        # test
        self.performance_manager.update_account_log(valid_account_info)

        # validate 
        self.assertEqual(self.performance_manager.account_log[0], valid_account_info)
        self.mock_logger.info.assert_called_once_with(f"\nAccount Log Updated: {valid_account_info}")

if __name__ == "__main__":
    unittest.main()