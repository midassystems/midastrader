import unittest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from midas.shared.orders import Action, OrderType
from midas.shared.signal import  TradeInstruction
from midas.engine.command.parameters import Parameters
from midas.shared.trade import Trade
from midas.shared.account import Account, EquityDetails
from midas.shared.market_data import MarketData, BarData, QuoteData,  MarketDataType
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, SignalEvent
from midas.engine.performance.base_manager import BasePerformanceManager, TradesManager, EquityManager

class TestTradesManager(unittest.TestCase):    
    def setUp(self):
        # TradesManager object
        self.trades_manager = TradesManager()
        self.trades_manager.trades = [
            Trade(timestamp=np.uint64(1712066400000000000), trade_id=13, leg_id=1, ticker='HE.n.0', quantity=-63, avg_price=104.425, trade_value=-2631510.0, trade_cost=354511.71, action='SHORT', fees=-53.55), 
            Trade(timestamp=np.uint64(1712066400000000000), trade_id=13, leg_id=2, ticker='ZC.n.0', quantity=114, avg_price=431.5, trade_value=2459550.0, trade_cost=236591.04, action='LONG', fees=-96.9), 
            Trade(timestamp=np.uint64(1712235600000000000), trade_id=13, leg_id=1, ticker='HE.n.0', quantity=63, avg_price=104.55, trade_value=2634660.0, trade_cost=354511.71, action='COVER', fees=-53.55), 
            Trade(timestamp=np.uint64(1712235600000000000), trade_id=13, leg_id=2, ticker='ZC.n.0', quantity=-114, avg_price=433.0, trade_value=-2468100.0, trade_cost=236591.04, action='SELL', fees=-96.9), 
            Trade(timestamp=np.uint64(1712336400000000000), trade_id=14, leg_id=1, ticker='HE.n.0', quantity=-63, avg_price=107.925, trade_value=-2719710.0, trade_cost=354511.71, action='SHORT', fees=-53.55),
            Trade(timestamp=np.uint64(1712336400000000000), trade_id=14, leg_id=2, ticker='ZC.n.0', quantity=114, avg_price=433.25, trade_value=2469525.0, trade_cost=236591.04, action='LONG', fees=-96.9), 
            Trade(timestamp=np.uint64(1712754000000000000), trade_id=14, leg_id=1, ticker='HE.n.0', quantity=63, avg_price=107.875, trade_value=2718450.0, trade_cost=354511.71, action='COVER', fees=-53.55), 
            Trade(timestamp=np.uint64(1712754000000000000), trade_id=14, leg_id=2, ticker='ZC.n.0', quantity=-114, avg_price=433.5, trade_value=-2470950.0, trade_cost=236591.04, action='SELL', fees=-96.9), 
            Trade(timestamp=np.uint64(1712926800000000000), trade_id=15, leg_id=1, ticker='HE.n.0', quantity=63, avg_price=105.25, trade_value=2652300.0, trade_cost=354511.71, action='LONG', fees=-53.55), 
            Trade(timestamp=np.uint64(1712926800000000000), trade_id=15, leg_id=2, ticker='ZC.n.0', quantity=-115, avg_price=446.25, trade_value=-2565937.5, trade_cost=238666.4, action='SHORT', fees=-97.75), 
            Trade(timestamp=np.uint64(1713272400000000000), trade_id=15, leg_id=1, ticker='HE.n.0', quantity=-63, avg_price=102.775, trade_value=-2589930.0, trade_cost=354511.71, action='SELL', fees=-53.55), 
            Trade(timestamp=np.uint64(1713272400000000000), trade_id=15, leg_id=2, ticker='ZC.n.0', quantity=115, avg_price=441.75, trade_value=2540062.5, trade_cost=238666.4, action='COVER', fees=-97.75), 
        ]

        self.pnl = np.array([13466.7, -63784.2, 103997.8 ,-83166.9, 63782.7, 7025.7, -16613.5, 531.6, 31406.6, 53848.1, 48177.8, 29275.1, 5099.1, 2384.1, -36797.6 ,28295.1])
        
    
    def test_aggregate_trades(self):
        # Test
        aggregated_df = self.trades_manager._aggregate_trades()

        # Expected
        data = {
                'trade_id': [13, 14, 15],
                'start_date': [np.uint64(1712066400000000000), np.uint64(1712336400000000000), np.uint64(1712926800000000000)],
                'end_date': [np.uint64(1712235600000000000), np.uint64(1712754000000000000), np.uint64(1713272400000000000)],
                'entry_value': [-171960.0, -250185.0, 86362.5],
                'exit_value': [166560.0, 247500.0, -49867.5],
                'entry_cost': [591102.75, 591102.75, 593178.11],
                'exit_cost': [591102.75, 591102.75, 593178.11],
                'fees': [-300.9, -300.9, -302.6],
                'gain/loss': [5400.0, 2685.0, -36495.0],
                'pnl': [5099.1, 2384.1, -36797.6],
                'pnl_percentage': [0.862642, 0.403331, -6.203466]
            }
        expected_df = pd.DataFrame(data)


        # Validate
        pd.testing.assert_frame_equal(aggregated_df, expected_df)

    def test_calculate_statistics(self):
        # Test
        result = self.trades_manager.calculate_trade_statistics()

        # Expected
        keys = ["total_trades", 
                "total_winning_trades", 
                "total_losing_trades",
                "avg_profit",
                "avg_profit_percent", 
                "avg_gain",
                "avg_gain_percent",
                "avg_loss",
                "avg_loss_percent",
                "profitability_ratio",
                "profit_factor",
                "profit_and_loss_ratio",
                "total_fees"
            ]
        
        # Validate
        for key in keys:
            self.assertIsNotNone(result[key])

    def test_total_trades(self):
        expected_total_trades = 16

        # Test
        total_trades = self.trades_manager.total_trades(self.pnl)

        # Validate
        self.assertEqual(total_trades, expected_total_trades)

    # Total Winning Trades
    def test_total_winning_trades(self):
        expected_winning_trades = 12

        # Test
        total_winning_trades = self.trades_manager.total_winning_trades(self.pnl)

        # Validate
        self.assertEqual(total_winning_trades, expected_winning_trades)

    # Total Losing Trades
    def test_total_losing_trades(self):
        expected_losing_trades = 4
        
        # Test
        total_losing_trades = self.trades_manager.total_losing_trades(self.pnl)

        # Validate
        self.assertEqual(total_losing_trades, expected_losing_trades)

    # Total Avg Win Percent
    def test_avg_win_return_rate(self):
        expected_avg_win = 32274.20

        # Test
        avg_win_return_rate = self.trades_manager.avg_gain(self.pnl)

        # Validate
        self.assertAlmostEqual(avg_win_return_rate, expected_avg_win, places=4)

    # Total avg_loss_return_rate
    def test_avg_loss_return_rate(self):
        expected_avg_loss = -50090.55

        # Test
        avg_loss_return_rate = self.trades_manager.avg_loss(self.pnl)

        # Validate
        self.assertAlmostEqual(avg_loss_return_rate, expected_avg_loss, places=4)

    # Percent Profitable
    def test_profitability_ratio(self):
        expected_profitability_ratio = 12/16 

        # Test
        profitability_ratio = TradesManager.profitability_ratio(self.pnl)

        # Validate
        self.assertEqual(profitability_ratio, expected_profitability_ratio)

    # Avg Trade Profit
    def test_avg_trade_profit(self):
        expected_avg_trade_profit = 11683.0125

        # Test
        average_trade_profit = self.trades_manager.avg_profit(self.pnl)

        # Validate
        self.assertEqual(average_trade_profit, expected_avg_trade_profit)

    # Profit Factor
    def test_profit_factor(self):
        expected_profit_factor = 1.933

        # Test
        profit_factor = self.trades_manager.profit_factor(self.pnl)

        # Validate
        self.assertEqual(profit_factor, expected_profit_factor)

    # Profit & Loss Ratio
    def test_profit_and_loss_ratio(self):
        expected_pnl_ratio = 0.6443

        # Test
        profit_and_loss_ratio = self.trades_manager.profit_and_loss_ratio(self.pnl)

        # Validate
        self.assertEqual(profit_and_loss_ratio, expected_pnl_ratio)

class TestEquityManager(unittest.TestCase):    
    def setUp(self) -> None:
        # Equitymanager object
        self.equity_manager = EquityManager()
        self.equity_manager.equity_value = [
            {'timestamp': 1713888000000000000, 'equity_value': 1189792.75}, 
            {'timestamp': 1713891600000000000, 'equity_value': 1193107.75}, 
            {'timestamp': 1713895200000000000, 'equity_value': 1192942.75}, 
            {'timestamp': 1713963600000000000, 'equity_value': 1198612.75}, 
            {'timestamp': 1713967200000000000, 'equity_value': 1179022.75}, 
            {'timestamp': 1713970800000000000, 'equity_value': 1182667.75}, 
            {'timestamp': 1713974400000000000, 'equity_value': 1185022.75}, 
            {'timestamp': 1713978000000000000, 'equity_value': 1175647.75}, 
            {'timestamp': 1713981600000000000, 'equity_value': 1174552.75}, 
            {'timestamp': 1714050000000000000, 'equity_value': 1242757.75}, 
            {'timestamp': 1714050000000000000, 'equity_value': 1242607.3}, 
            {'timestamp': 1714053600000000000, 'equity_value': 1242607.3}, 
            {'timestamp': 1714057200000000000, 'equity_value': 1242607.3}, 
            {'timestamp': 1714060800000000000, 'equity_value': 1242607.3}
        ]
        self.raw_equity_df = pd.DataFrame(self.equity_manager.equity_value)
        self.raw_equity_df.set_index("timestamp", inplace=True)


    def test_calculate_return_and_drawdown(self):
        # Test
        result = self.equity_manager._calculate_return_and_drawdown(self.raw_equity_df)

        # Expected
        data = {
            'timestamp': [
                1713888000000000000, 1713891600000000000, 1713895200000000000, 1713963600000000000,
                1713967200000000000, 1713970800000000000, 1713974400000000000, 1713978000000000000,
                1713981600000000000, 1714050000000000000, 1714050000000000000, 1714053600000000000,
                1714057200000000000, 1714060800000000000
            ],
            'equity_value': [
                1189792.75, 1193107.75, 1192942.75, 1198612.75, 1179022.75, 1182667.75, 1185022.75,
                1175647.75, 1174552.75, 1242757.75, 1242607.30, 1242607.30, 1242607.30, 1242607.30
            ],
            'period_return': [
                0.000000, 0.002786, -0.000138, 0.004753, -0.016344, 0.003092, 0.001991, -0.007911,
                -0.000931, 0.058069, -0.000121, 0.000000, 0.000000, 0.000000
            ],
            'cumulative_return': [
                0.000000, 0.002786, 0.002648, 0.007413, -0.009052, -0.005988, -0.004009, -0.011889,
                -0.012809, 0.044516, 0.044390, 0.044390, 0.044390, 0.044390
            ],
            'drawdown': [0.0, 0.0, -0.000138, 0.0, -0.016344, -0.013303, -0.011338, -0.019159, -0.020072, 0.0, -0.000121, -0.000121, -0.000121, -0.000121]
            
        }
        expected_df = pd.DataFrame(data)
        expected_df.set_index('timestamp', inplace=True)

        # Validate
        pd.testing.assert_frame_equal(result, expected_df)
 
    def test_calculate_statistics(self):
        # Test 
        result = self.equity_manager.calculate_equity_statistics()

        # Expected
        keys = [
                "net_profit",
                "beginning_equity",
                "ending_equity",
                "total_return",
                "daily_standard_deviation_percentage",
                "annual_standard_deviation_percentage",
                "max_drawdown_percentage_period",
                "max_drawdown_percentage_daily",
                "sharpe_ratio",
                "sortino_ratio"  
            ]

        # Validate
        for key in keys:
            self.assertIsNotNone(result[key])


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
            trade_cost = 10000,
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
        self.mock_logger.info.assert_called_once_with('\nTRADES UPDATED:\n  Timestamp: 16555000\n  Trade ID: 1\n  Leg ID: 2\n  Ticker: HEJ4\n  Quantity: 10\n  Avg Price: 85.98\n  Trade Value: 100000\n  Trade Cost: 10000\n  Action: BUY\n  Fees: 9.87\n\n')

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
        account_info = Account(
            timestamp=np.uint64(1650000000),        
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

if __name__ == "__main__":
    unittest.main()
