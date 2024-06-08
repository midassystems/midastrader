import unittest
import numpy as np
from queue import Queue
from decimal import Decimal
from datetime import datetime
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from midas.engine.command.config import Mode
from midas.shared.signal import TradeInstruction
from midas.shared.trade import Trade, ExecutionDetails
from midas.shared.orders import OrderType, Action , MarketOrder
from midas.shared.market_data import MarketData, BarData, QuoteData
from midas.engine.command.controller import LiveEventController, BacktestEventController
from midas.engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, EODEvent

class TestLiveController(unittest.TestCase):
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
    def test_handle_event_market_event(self):
        self.event_controller = LiveEventController(self.mock_config)
        bar = BarData(ticker="AAPL", 
                        timestamp=np.uint64(1707221160000000000),
                        open=Decimal(100.990808),
                        high=Decimal(1111.9998),
                        low=Decimal(99.990898),
                        close=Decimal(105.9089787),
                        volume=np.uint64(100000909))
        
        market_event = MarketEvent(np.uint64(1707221160000000000), data = {'AAPL': bar} )
        
        # test
        self.event_controller._handle_event(market_event)

        # validate
        self.mock_config.strategy.handle_market_data.assert_called()

    def test_handle_event_signal_event(self):
        self.event_controller = LiveEventController(self.mock_config)
        
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
        self.event_controller._handle_event(signal_event)

        # validate
        self.mock_config.performance_manager.update_signals.assert_called_once_with(signal_event)
        self.mock_config.order_manager.on_signal.assert_called_once_with(signal_event)

    def test_handle_event_order_event(self):
        self.event_controller = LiveEventController(self.mock_config)
        order_event = OrderEvent(timestamp=np.uint64(1651500000),
                           trade_id=6,
                           leg_id=2,
                           action=Action.LONG,
                           order=MarketOrder(Action.LONG,10),
                           contract=Contract())
        
        # test
        self.event_controller._handle_event(order_event)

        # validate
        self.mock_config.broker_client.on_order.assert_called_once_with(order_event)

class TestBacktestController(unittest.TestCase):
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
    def test_run(self):
        self.mock_config.mode = Mode.BACKTEST
        self.event_controller = BacktestEventController(self.mock_config)
        self.event_controller.logger = Mock()
        self.event_controller.hist_data_client.data_stream.side_effect = [True, False]
        self.mock_config.event_queue.put("3")
        self.event_controller._handle_event = Mock()

        # test
        self.event_controller.run()

        # valdiate
        self.assertEqual(self.event_controller.logger.info.call_count, 3)
        self.assertEqual(self.event_controller.hist_data_client.data_stream.call_count, 2)
        self.event_controller._handle_event.assert_called_once_with("3")
        self.event_controller.broker_client.eod_update.assert_called_once()
        self.event_controller.broker_client.liquidate_positions()
        self.event_controller.performance_manager.calculate_statistics() 
        self.event_controller.performance_manager.save()

    def test_handle_event_market_event(self):
        self.event_controller = BacktestEventController(self.mock_config)
        bar = BarData(ticker="AAPL", 
                        timestamp=np.uint64(1707221160000000000),
                        open=Decimal(100.990808),
                        high=Decimal(1111.9998),
                        low=Decimal(99.990898),
                        close=Decimal(105.9089787),
                        volume=np.uint64(100000909))
        
        market_event = MarketEvent(np.uint64(1707221160000000000), data = {'AAPL': bar} )
        
        # test
        self.event_controller._handle_event(market_event)

        # validate
        self.mock_config.broker_client.update_equity_value.assert_called()
        self.mock_config.strategy.handle_market_data.assert_called()

    def test_handle_event_signal_event(self):
        self.event_controller = BacktestEventController(self.mock_config)
        
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
        self.event_controller._handle_event(signal_event)

        # validate
        self.mock_config.performance_manager.update_signals.assert_called_once_with(signal_event)
        self.mock_config.order_manager.on_signal.assert_called_once_with(signal_event)

    def test_handle_event_order_event(self):
        self.event_controller = BacktestEventController(self.mock_config)
        order_event = OrderEvent(timestamp=np.uint64(1651500000),
                           trade_id=6,
                           leg_id=2,
                           action=Action.LONG,
                           order=MarketOrder(Action.LONG,10),
                           contract=Contract())
        
        # test
        self.event_controller._handle_event(order_event)

        # validate
        self.mock_config.broker_client.on_order.assert_called_once_with(order_event)

    def test_handle_event_execution_event(self):
        self.event_controller = BacktestEventController(self.mock_config)
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
        
        # test
        self.event_controller._handle_event(execution_event)

        # validate
        self.mock_config.broker_client.on_execution.assert_called_once_with(execution_event)

    def test_run_backtest_EOD_event(self):
        self.event_controller = BacktestEventController(self.mock_config)        
        eod_event = EODEvent(datetime(2024,10, 1))
        
        # test
        self.event_controller._handle_event(eod_event)

        # validate
        self.assertEqual(self.mock_config.broker_client.eod_update.call_count, 1)

if __name__ == "__main__":

    unittest.main()