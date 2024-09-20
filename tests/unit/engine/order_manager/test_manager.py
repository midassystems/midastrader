import unittest
import numpy as np
from unittest.mock import Mock
from unittest.mock import patch
from ibapi.contract import Contract
from midas.shared.account import Account
from midas.shared.market_data import BarData
from midas.shared.signal import TradeInstruction
from midas.engine.order_manager import OrderManager
from midas.engine.events import MarketEvent, SignalEvent, OrderEvent
from midas.shared.symbol import Equity, Currency,Venue, Future, Industry, ContractUnits
from midas.shared.orders import MarketOrder, LimitOrder, StopLoss, OrderType, Action


class TestOrderManager(unittest.TestCase):
    def setUp(self) -> None:
        # Mock methods
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        
        # Test symbols
        self.symbols_map = {'HEJ4' : Future(ticker = "HEJ4",
                                            data_ticker = "HE.n.0",
                                            currency = Currency.USD,  
                                            exchange = Venue.CME,  
                                            fees = 0.85,  
                                            initial_margin =4564.17,
                                            quantity_multiplier=40000,
                                            price_multiplier=0.01,
                                            product_code="HE",
                                            product_name="Lean Hogs",
                                            industry=Industry.AGRICULTURE,
                                            contract_size=40000,
                                            contract_units=ContractUnits.POUNDS,
                                            tick_size=0.00025,
                                            min_price_fluctuation=10,
                                            continuous=False,
                                            lastTradeDateOrContractMonth="202404"),
                                    'AAPL' : Equity(ticker="AAPL",
                                                    currency = Currency.USD  ,
                                                    exchange = Venue.NASDAQ  ,
                                                    fees = 0.1,
                                                    initial_margin = 0,
                                                    quantity_multiplier=1,
                                                    price_multiplier=1,
                                                    data_ticker = "AAPL2",
                                                    company_name = "Apple Inc.",
                                                    industry=Industry.TECHNOLOGY,
                                                    market_cap=10000000000.99,
                                                    shares_outstanding=1937476363)}
        
        # Test account
        self.mock_portfolio_server.account = Account(
                            timestamp=np.uint64(1704214800000000000),
                            full_available_funds=502398.7799999999,
                            full_init_margin_req=497474.57,
                            net_liquidation=999873.3499999999,
                            unrealized_pnl=1234,
                            full_maint_margin_req=12345,
                            excess_liquidity=9876543,
                            currency="USD",
                            buying_power=765432,
                            futures_pnl=76543,
                            total_cash_balance=4321,
                        )
        
        # OrderManager instance
        self.order_manager = OrderManager(self.symbols_map, 
                                          self.mock_event_queue, 
                                          self.mock_order_book, 
                                          self.mock_portfolio_server, 
                                          self.mock_logger)

        # Test Data
        self.timestamp = np.uint64(1651500000)
        self.trade_capital = 10000
        self.trade_equity = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5,
                                                quantity=2)
        self.trade_fut = TradeInstruction(ticker = 'HEJ4',
                                                order_type = OrderType.MARKET,
                                                action = Action.SHORT,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5, 
                                                quantity=-2)
        self.trade_instructions = [self.trade_equity,self.trade_fut]
        self.signal_event = SignalEvent(self.timestamp, self.trade_instructions)                   
        
    # Basic Validation
    def test_create_marketorder_valid(self):
        trade_instructions = self.trade_equity 

        # Test 
        order = self.order_manager._create_order(trade_instructions)
        
        # Validation
        self.assertEqual(type(order), MarketOrder)
        self.assertEqual(order.order.action,trade_instructions.action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(trade_instructions.quantity))

    def test_create_limitorder_valid(self):
        trade_instructions = TradeInstruction(ticker = 'HEJ4',
                                                order_type = OrderType.LIMIT,
                                                action = Action.SHORT,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5, 
                                                quantity=-2,
                                                limit_price=90)

        # Test 
        order = self.order_manager._create_order(trade_instructions)
        
        # Validation
        self.assertEqual(type(order), LimitOrder)
        self.assertEqual(order.order.action,trade_instructions.action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(trade_instructions.quantity))
        self.assertEqual(order.order.lmtPrice, trade_instructions.limit_price)

    def test_create_stoplossorder_valid(self):
        trade_instructions = TradeInstruction(ticker = 'HEJ4',
                                                order_type = OrderType.STOPLOSS,
                                                action = Action.SHORT,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5, 
                                                quantity=-2, 
                                                aux_price=90)

        # Test
        order = self.order_manager._create_order(trade_instructions)
        
        # Validation
        self.assertEqual(type(order), StopLoss)
        self.assertEqual(order.order.action,trade_instructions.action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(trade_instructions.quantity))
        self.assertEqual(order.order.auxPrice, trade_instructions.aux_price)

    def test_handle_signal_sufficient_captial(self):
        self.mock_portfolio_server.capital= 10000
        self.mock_order_book.current_price.return_value = 150
        self.mock_portfolio_server.account.full_init_margin_req = 1000
        self.mock_portfolio_server.account.full_available_funds = 50000

        # Test Order Set b/c funds available
        with patch.object(self.order_manager, '_set_order') as mocked_method:
            self.order_manager._handle_signal(timestamp=self.timestamp, trade_instructions=self.trade_instructions)
            mocked_method.assert_called() # set_order should be called

    def test_handle_signal_insufficient_capital(self):
        self.mock_portfolio_server.capital= 100
        self.mock_order_book.current_price.return_value = 150
        self.mock_portfolio_server.account.full_init_margin_req = 1000
        self.mock_portfolio_server.account.full_available_funds = 100

        # Test Order set b/c no funds currently available
        with patch.object(self.order_manager, '_set_order') as mocked_method:
            self.order_manager._handle_signal(timestamp=self.timestamp, trade_instructions=self.trade_instructions)
            self.assertFalse(mocked_method.called) # set_order should not be called 

    def test_on_signal_valid(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = ["AAPL"]
        
        # Test handle_signal called 
        with patch.object(self.order_manager, '_handle_signal') as mocked_method:
            self.order_manager.on_signal(self.signal_event)
            self.assertEqual(mocked_method.call_count, 0)

    def test_on_signal_without_active_orders(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = []

        # Test handle_signal called 
        with patch.object(self.order_manager, '_handle_signal') as mocked_method:
            self.order_manager.on_signal(self.signal_event)
            mocked_method.assert_called_once()

    def test_set_order(self):
        self.timestamp = np.uint64(1651500000)
        self.action = Action.LONG
        self.trade_id = 2
        self.leg_id =  6
        self.order = MarketOrder(action=self.action, quantity=10)
        self.contract = Contract()

        # Test
        self.order_manager._set_order(timestamp=self.timestamp,
                                      action=self.action,
                                      trade_id=self.trade_id,
                                      leg_id=self.leg_id,
                                      order=self.order,
                                      contract=self.contract)
        

        # Validation
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.") # check that event_queue.put() was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0]   # Get the argument with which event_queue.put was called
        self.assertIsInstance(called_with_arg, OrderEvent, "The argument is not an instance of SignalEvent") # check arguemnt in event_queue.put() was an Order event


if __name__ == "__main__":
    unittest.main()