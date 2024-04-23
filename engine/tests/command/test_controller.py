import os
import time
import signal
import unittest
import threading
import numpy as np
from decimal import Decimal
from queue import Queue
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from engine.command import EventController, Mode
from engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, EODEvent

from shared.signal import TradeInstruction
from shared.trade import Trade, ExecutionDetails
from shared.orders import OrderType, Action , MarketOrder
from shared.market_data import MarketData, BarData, QuoteData


#TODO: run live tests/ edge case

class TestController(unittest.TestCase):    
    def setUp(self) -> None:
        self.mock_config = Mock()
        self.mock_config.event_queue = Queue()
        self.mock_config.hist_data_client = Mock()
        self.mock_config.broker_client = Mock()
        self.mock_config.order_book = Mock()
        self.mock_config.strategy = Mock()
        self.mock_config.order_manager = Mock()
        self.mock_config.db_updater = Mock()
        self.mock_config.performance_manager = Mock()
    
    # Basic Validation
    def test_run_mode_live(self):
        self.mock_config.mode = Mode.LIVE
        self.event_controller = EventController(self.mock_config)

        with patch.object(self.event_controller, '_run_live') as mock_run_live:
            self.event_controller.run()
            mock_run_live.assert_called_once()

    def test_run_mode_backtest(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)

        with patch.object(self.event_controller, '_run_backtest') as mock_run_backtest:
            self.event_controller.run()
            mock_run_backtest.assert_called_once()

    def simulate_sigint(self):
        """Simulates the SIGINT signal reception after a short delay."""
        time.sleep(0.1)
        self.event_controller.signal_handler(signal.SIGINT, None)

    def test_run_backtest_market_event(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
        bar = BarData(ticker="AAPL", 
                        timestamp=np.uint64(1707221160000000000),
                        open=Decimal(100.990808),
                        high=Decimal(1111.9998),
                        low=Decimal(99.990898),
                        close=Decimal(105.9089787),
                        volume=np.uint64(100000909))
        
        market_event = MarketEvent(np.uint64(1707221160000000000), data = {'AAPL': bar} )
        
        self.mock_config.hist_data_client.data_stream.side_effect = [True, False]# Simulates one iterations then stop
        self.event_controller.event_queue.put(market_event)
        
        # Run the backtest
        self.event_controller._run_backtest()

        # Verify interactions
        self.mock_config.broker_client.update_equity_value.assert_called()
        self.mock_config.strategy.handle_market_data.assert_called()

    def test_run_backtest_signal_event(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
        
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
                        
        signal_event = SignalEvent(np.uint64(1651500000), 10000,self.valid_trade_instructions)
        
        self.mock_config.hist_data_client.data_stream.side_effect = [True, False]# Simulates one iterations then stop
        self.event_controller.event_queue.put(signal_event)
        
        # Run the backtest
        self.event_controller._run_backtest()

        # Verify interactions
        self.mock_config.performance_manager.update_signals.assert_called_once_with(signal_event)
        self.mock_config.order_manager.on_signal.assert_called_once_with(signal_event)

    def test_run_backtest_order_event(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
        order_event = OrderEvent(timestamp=np.uint64(1651500000),
                           trade_id=6,
                           leg_id=2,
                           action=Action.LONG,
                           order=MarketOrder(Action.LONG,10),
                           contract=Contract())
        
        self.mock_config.hist_data_client.data_stream.side_effect = [True, False]# Simulates one iterations then stop
        self.event_controller.event_queue.put(order_event)
        
        # Run the backtest
        self.event_controller._run_backtest()

        # Verify interactions
        self.mock_config.broker_client.on_order.assert_called_once_with(order_event)

    def test_run_backtest_execution_event(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
        
        self.valid_trade_details = ExecutionDetails(trade_id=1,
                      leg_id=2,
                      timestamp=1651500000,
                      ticker='HEJ4',
                      quantity=10,
                      price= 85.98,
                      cost=9000.90,
                      action= 'BUY', 
                      fees= 9.87)
        execution_event = ExecutionEvent(timestamp=np.uint64(1651500000),
                               trade_details=self.valid_trade_details,
                               action=Action.SELL,
                               contract=Contract())
        
        self.mock_config.hist_data_client.data_stream.side_effect = [True, False]# Simulates one iterations then stop
        self.event_controller.event_queue.put(execution_event)
        
        # Run the backtest
        self.event_controller._run_backtest()

        # Verify interactions
        self.mock_config.broker_client.on_execution.assert_called_once_with(execution_event)

    def test_run_backtest_EOD_event(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
        self.mock_config.hist_data_client.data_stream.side_effect = [True, False]# Simulates one iterations then stop
        
        eod_event = EODEvent(11111)
        self.event_controller.event_queue.put(eod_event)
        
        # Run the backtest
        self.event_controller._run_backtest()

        # Verify interactions
        self.assertEqual(self.mock_config.broker_client.eod_update.call_count, 2)

    def test_wrap_up_backtest(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = EventController(self.mock_config)
    
        self.mock_config.hist_data_client.data_stream.side_effect = [False]# Simulates one iterations then stop

        # Run the backtest
        self.event_controller._run_backtest()

        self.assertTrue(self.mock_config.broker_client.eod_update.called)
        self.assertTrue(self.mock_config.broker_client.liquidate_positions.called)
        self.assertTrue(self.mock_config.performance_manager.calculate_statistics.called)
        self.assertTrue(self.mock_config.performance_manager.create_backtest.called)
    
    # ---- Have to exit is Ctrl + C or will hang ---- 
    # def test_run_live(self):
    #     self.mock_config.mode = Mode.LIVE
    #     self.event_controller = EventController(self.mock_config)
        
    #     market_event = MarketEvent(timestamp=1651500000,
    #                         data = {'AAPL': BarData(timestamp = 1651500000,
    #                                                     open = 80.90,
    #                                                     close = 9000.90,
    #                                                     high = 75.90,
    #                                                     low = 8800.09,
    #                                                     volume = 880000)}
    #                         )
        
    #     self.mock_config.strategy.handle_market_data.return_value = False
    #     self.event_controller.event_queue.put(market_event)
        
    #     # Run the backtest
    #     self.event_controller._run_live()

    #     # Verify interactions
    #     self.mock_config.strategy.handle_market_data.assert_called()

    # def test_run_live_stops_gracefully1(self):
    #     self.mock_config.mode = Mode.LIVE
    #     self.event_controller = EventController(self.mock_config)
    #     self.event_controller._run_live()

    #     # Verify that the signal handler was called and the loop exited
    #     self.mock_config.logger.info.assert_called_with("Live trading stopped. Performing cleanup...")
    #     self.mock_config.db_updater.delete_session.assert_called_once()
    #     # self.mock_config.performance_manager.calculate_statistics.assert_called_once()
    #     self.mock_config.performance_manager.create_live_session.assert_called_once()



if __name__ == "__main__":

    unittest.main()