import unittest
import numpy as np
from unittest.mock import Mock
from unittest.mock import patch
from ibapi.contract import Contract

from engine.order_manager import OrderManager
from engine.events import MarketEvent, SignalEvent, OrderEvent

from shared.market_data import BarData
from shared.signal import TradeInstruction
from shared.symbol import Equity, Currency,Venue, Future, Industry, ContractUnits
from shared.orders import MarketOrder, LimitOrder, StopLoss, OrderType, Action

# TODO : Edge Cases

class TestOrderManager(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        
        self.valid_symbols_map = {'HEJ4' : Future(ticker = "HEJ4",
                                            data_ticker = "HE.n.0",
                                            currency = Currency.USD,  
                                            exchange = Venue.CME,  
                                            fees = 0.85,  
                                            initialMargin =4564.17,
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
                                                    initialMargin = 0,
                                                    quantity_multiplier=1,
                                                    price_multiplier=1,
                                                    data_ticker = "AAPL2",
                                                    company_name = "Apple Inc.",
                                                    industry=Industry.TECHNOLOGY,
                                                    market_cap=10000000000.99,
                                                    shares_outstanding=1937476363)}
        
        self.mock_portfolio_server.account = {'FullAvailableFunds': 10000,
                                                'FullInitMarginReq': 5000,
                                                'UnrealizedPnL': 1000}

        self.order_manager = OrderManager(self.valid_symbols_map, self.mock_event_queue, self.mock_order_book, self.mock_portfolio_server, self.mock_logger)


        # Test Data
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_trade_capital = 10000
        self.valid_trade_equity = TradeInstruction(ticker = 'AAPL',
                                                order_type = OrderType.MARKET,
                                                action = Action.LONG,
                                                trade_id = 2,
                                                leg_id =  5,
                                                weight = 0.5)
        self.valid_trade_fut = TradeInstruction(ticker = 'HEJ4',
                                                order_type = OrderType.MARKET,
                                                action = Action.SHORT,
                                                trade_id = 2,
                                                leg_id =  6,
                                                weight = 0.5)
        self.valid_trade_instructions = [self.valid_trade_equity,self.valid_trade_fut]
        self.valid_signal_event = SignalEvent(self.valid_timestamp,self.valid_trade_capital, self.valid_trade_instructions)                   
        
    # Basic Validation
    def test_create_marketorder_valid(self):
        action = Action.LONG
        quantity=-100

        # Test 
        order = self.order_manager._create_order(order_type=OrderType.MARKET, action=action, quantity=quantity)
        
        # Validation
        self.assertEqual(type(order), MarketOrder)
        self.assertEqual(order.order.action,action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(quantity))

    def test_create_limitorder_valid(self):
        action = Action.SHORT
        quantity=-100
        limit_price = 90

        # Test 
        order = self.order_manager._create_order(order_type=OrderType.LIMIT, action=action, quantity=quantity, limit_price=limit_price)
        
        # Validation
        self.assertEqual(type(order), LimitOrder)
        self.assertEqual(order.order.action,action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(quantity))
        self.assertEqual(order.order.lmtPrice, limit_price)

    def test_create_stoplossorder_valid(self):
        action = Action.SELL
        quantity=-100
        aux_price = 90

        # Test
        order = self.order_manager._create_order(order_type=OrderType.STOPLOSS, action=action, quantity=quantity, aux_price=aux_price)
        
        # Validation
        self.assertEqual(type(order), StopLoss)
        self.assertEqual(order.order.action,action.to_broker_standard())
        self.assertEqual(order.order.totalQuantity, abs(quantity))
        self.assertEqual(order.order.auxPrice, aux_price)

    def test_order_quantity_valid(self):
        order_allocation=10000
        current_price=50
        quantity_multiplier=100
        price_multiplier=0.01

        # Test Long Quantity
        quantity = self.order_manager._order_quantity(action=Action.LONG, 
                                                      ticker='AAPL', 
                                                      order_allocation=order_allocation, 
                                                      current_price=current_price, 
                                                      quantity_multiplier=quantity_multiplier,
                                                      price_multiplier=price_multiplier)
        
        # Validation
        self.assertEqual(abs(quantity), order_allocation / (current_price * price_multiplier * quantity_multiplier))

        # Test Short Quantity
        quantity = self.order_manager._order_quantity(action=Action.SHORT,
                                                      ticker='AAPL', 
                                                      order_allocation=order_allocation, 
                                                      current_price=current_price, 
                                                      quantity_multiplier=quantity_multiplier,
                                                      price_multiplier=price_multiplier)
        
        self.assertEqual(abs(quantity),order_allocation / (current_price * price_multiplier * quantity_multiplier))

        # Test Sell Quantity
        self.mock_portfolio_server.positions = {'AAPL': Mock(quantity=10)}
        quantity = self.order_manager._order_quantity(action=Action.SELL,
                                                      ticker='AAPL', 
                                                      order_allocation=order_allocation, 
                                                      current_price=current_price, 
                                                      quantity_multiplier=quantity_multiplier,
                                                      price_multiplier=price_multiplier)
        # Validation
        self.assertEqual(abs(quantity),10)

        # Test Cover Quantity
        self.mock_portfolio_server.positions = {'AAPL': Mock(quantity=-10)}
        quantity = self.order_manager._order_quantity(action=Action.COVER,
                                            ticker='AAPL', 
                                            order_allocation=order_allocation, 
                                            current_price=current_price, 
                                            quantity_multiplier=quantity_multiplier,
                                            price_multiplier=price_multiplier)
        # Validation
        self.assertEqual(abs(quantity),10)

    def test_order_details_valid(self):
        weight = 0.5
        position_allocation = 10000.0
        self.valid_future_instructions = TradeInstruction(ticker = 'HEJ4',
                                                            order_type = OrderType.MARKET,
                                                            action = Action.LONG,
                                                            trade_id = 1,
                                                            leg_id =  1,
                                                            weight = weight)

        self.mock_order_book.current_price.return_value = 150.0
        expected_quantity = (weight * position_allocation)/ (150.0*self.valid_symbols_map['HEJ4'].price_multiplier *self.valid_symbols_map['HEJ4'].quantity_multiplier )
        
        # Test
        order = self.order_manager._order_details(self.valid_future_instructions, position_allocation)
        
        # Validation
        self.assertEqual(type(order), MarketOrder)
        self.assertEqual(order.order.totalQuantity,expected_quantity)

    def test_future_order_value(self):
        quantity = 10000.0
        ticker ='HEJ4'
        
        # Test
        order_value = self.order_manager._future_order_value(quantity, ticker)

        # Validation
        self.assertEqual(type(order_value), float)
        self.assertEqual(order_value, quantity*self.valid_symbols_map[ticker].initialMargin)

    def test_equity_order_value(self):
        quantity = 10000.0
        ticker = 'AAPL'
        self.mock_order_book.current_price.return_value = 150

        # Test
        order_value = self.order_manager._equity_order_value(quantity, ticker)

        # Validation
        self.assertEqual(type(order_value), float)
        self.assertEqual(order_value, quantity * 150)

    def test_handle_signal_valid(self):
        self.mock_order_book.current_price.return_value = 150
        self.mock_portfolio_server.account['FullInitMarginReq'] = 1000
        self.mock_portfolio_server.account['FullAvailableFunds'] = 50000

        # Test Order Set b/c funds available
        with patch.object(self.order_manager, '_set_order') as mocked_method:
            self.order_manager._handle_signal(timestamp=self.valid_timestamp,trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade_instructions)
            mocked_method.assert_called() # set_order should be called

        self.mock_portfolio_server.account['FullInitMarginReq'] = 1000
        self.mock_portfolio_server.account['FullAvailableFunds'] = 1000

        # Test Order set b/c no funds currently available
        with patch.object(self.order_manager, '_set_order') as mocked_method:
            self.order_manager._handle_signal(timestamp=self.valid_timestamp,trade_capital=self.valid_trade_capital, trade_instructions=self.valid_trade_instructions)
            self.assertFalse(mocked_method.called) # set_order should not be called 

    def test_on_signal_valid(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = ["AAPL"]
        # Test handle_signal called 
        with patch.object(self.order_manager, '_handle_signal') as mocked_method:
            self.order_manager.on_signal(self.valid_signal_event)
            self.assertEqual(mocked_method.call_count, 0)

    def test_on_signal_without_active_orders(self):
        self.mock_portfolio_server.get_active_order_tickers.return_value = []

        # Test handle_signal called 
        with patch.object(self.order_manager, '_handle_signal') as mocked_method:
            self.order_manager.on_signal(self.valid_signal_event)
            mocked_method.assert_called_once()

    def test_set_order(self):
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(action=self.valid_action, quantity=10)
        self.valid_contract = Contract()

        # Test
        self.order_manager._set_order(timestamp=self.valid_timestamp,
                                      action=self.valid_action,
                                      trade_id=self.valid_trade_id,
                                      leg_id=self.valid_leg_id,
                                      order=self.valid_order,
                                      contract=self.valid_contract)
        

        # Validation
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.") # check that event_queue.put() was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0]   # Get the argument with which event_queue.put was called
        self.assertIsInstance(called_with_arg, OrderEvent, "The argument is not an instance of SignalEvent") # check arguemnt in event_queue.put() was an Order event

    # Type/Constraint Check 
    def test_create_order_invlaid_ordertype(self):
        action = Action.LONG
        quantity=-100
        # Test
        with self.assertRaisesRegex( RuntimeError,"OrderType not of valid type"):
            self.order_manager._create_order(order_type='invalid', action=action, quantity=quantity)
            
    def test_create_order_error_in_order_class(self):
        action = Action.LONG
        quantity=-100
        # Test
        with self.assertRaisesRegex(RuntimeError,"Failed to create or queue SignalEvent due to input error"):
            self.order_manager._create_order(order_type=OrderType.MARKET, action='LONG', quantity=quantity)


if __name__ == "__main__":
    unittest.main()