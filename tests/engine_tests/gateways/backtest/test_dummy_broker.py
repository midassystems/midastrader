import unittest
import numpy as np
from ibapi.order import Order
from contextlib import ExitStack
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from midas.engine.order_book import OrderBook
from midas.engine.events import ExecutionEvent
from midas.engine.gateways.backtest.dummy_broker import DummyBroker, PositionDetails, ExecutionDetails

from midas.shared.signal import TradeInstruction
from midas.shared.orders import Action, BaseOrder, MarketOrder
from midas.shared.portfolio import AccountDetails, EquityDetails
from midas.shared.symbol import Symbol, Future, Equity, Currency,Venue, Future, ContractUnits, Industry

#TODO : edge cases/ integration

class TestDummyClient(unittest.TestCase):
    def setUp(self) -> None:
        # Instantiate Dummy Client
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()
        self.valid_capital = 100000
        self.valid_slippage_factor = 2
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
        
        self.dummy_broker = DummyBroker(self.valid_symbols_map, self.mock_event_queue, self.mock_order_book, self.valid_capital, self.mock_logger, self.valid_slippage_factor)

    # Basic Validation
    def test_calculate_slippage_price(self):
        tick_size = 1
        current_price = 10

        action = Action.LONG
        # test
        adjusted_price = self.dummy_broker._slippage_adjust_price(tick_size, current_price, action)
        # validate
        self.assertIsInstance(adjusted_price, (float,int))
        self.assertEqual(adjusted_price, current_price + (tick_size * self.valid_slippage_factor))

        action = Action.COVER
        # test
        adjusted_price = self.dummy_broker._slippage_adjust_price(tick_size, current_price, action)
        # validate
        self.assertIsInstance(adjusted_price, (float,int))
        self.assertEqual(adjusted_price, current_price + (tick_size * self.valid_slippage_factor))

        action = Action.SHORT
        # test
        adjusted_price = self.dummy_broker._slippage_adjust_price(tick_size, current_price, action)
        # validate
        self.assertIsInstance(adjusted_price, (float,int))
        self.assertEqual(adjusted_price, current_price - (tick_size * self.valid_slippage_factor))

        action = Action.SELL
        # test
        adjusted_price = self.dummy_broker._slippage_adjust_price(tick_size, current_price, action)
        # validate
        self.assertIsInstance(adjusted_price, (float,int))
        self.assertEqual(adjusted_price, current_price - (tick_size * self.valid_slippage_factor))

    def test_calculate_commission_fees(self):
        contract = Contract()
        contract.symbol = 'HEJ4'
        quantity = 90

        # test
        commission = self.dummy_broker._calculate_commission_fees(contract, quantity)

        # validate
        self.assertIsInstance(commission, (float,int))
        self.assertEqual(commission, self.valid_symbols_map['HEJ4'].fees * quantity)

    def test_fill_price_future(self):
        contract = Contract()
        contract.symbol = 'HEJ4'
        contract.secType = 'FUT'
        action = Action.LONG
        self.mock_order_book.current_price.return_value = 100
        expected = self.mock_order_book.current_price.return_value + (self.valid_symbols_map['HEJ4'].tick_size * self.valid_slippage_factor)

        # test
        with patch.object(self.dummy_broker, '_slippage_adjust_price', return_value = expected):
            fill_price = self.dummy_broker._fill_price(contract, action)

        # validate
        self.assertIsInstance(fill_price, (float, int))
        self.assertEqual(fill_price, expected)

    def test_fill_price_equity(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.secType = 'STK'
        action = Action.LONG
        self.mock_order_book.current_price.return_value = 100
        expected = self.mock_order_book.current_price.return_value + (1 * self.valid_slippage_factor)

        # test
        with patch.object(self.dummy_broker, '_slippage_adjust_price', return_value = expected):
            fill_price = self.dummy_broker._fill_price(contract, action)

        # validate
        self.assertIsInstance(fill_price, (float, int))
        self.assertEqual(fill_price, expected)

    def test_calculate_trade_pnl_SHORT(self):
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier

        # Entry Values
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price = 50
        self.dummy_broker.positions[contract] = PositionDetails(
                                                    avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                                    quantity=entry_quantity, 
                                                    price_multiplier=price_multiplier,
                                                    quantity_multiplier=quantity_multiplier)

        # Exit Values
        exit_action = Action.COVER
        exit_quantity = 100
        exit_price = 45
        
        # test
        trade_pnl = self.dummy_broker._calculate_trade_pnl(self.dummy_broker.positions[contract], exit_price, exit_quantity)
        
        # expected
        expected_pnl =  (exit_price - entry_price) * price_multiplier * exit_quantity * quantity_multiplier * -1
        
        # validate
        self.assertEqual(trade_pnl, expected_pnl)

    def test_calculate_trade_pnl_LONG(self):
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier

        # Entry Values
        entry_action = Action.LONG
        entry_quantity = 100
        entry_price = 50
        self.dummy_broker.positions[contract] = PositionDetails(
                                            avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                            quantity=entry_quantity, 
                                            price_multiplier=price_multiplier,
                                            quantity_multiplier=quantity_multiplier)

        # Exit Values
        exit_action = Action.SELL
        exit_quantity = -100
        exit_price = 45
        # test
        trade_pnl = self.dummy_broker._calculate_trade_pnl(self.dummy_broker.positions[contract], exit_price, exit_quantity)

        # validate
        expected_pnl =  (exit_price - entry_price) * price_multiplier * exit_quantity * quantity_multiplier * -1
        
        # expected
        self.assertEqual(trade_pnl, expected_pnl)

    def test_calculate_trade_pnl_partial_exit(self):
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier

        # Entry Values
        entry_action = Action.LONG
        entry_quantity = 100
        entry_price = 50
        self.dummy_broker.positions[contract] = PositionDetails(
                                                    avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                                    quantity=entry_quantity, 
                                                    price_multiplier=price_multiplier,
                                                    quantity_multiplier=quantity_multiplier)


        # Exit Values
        exit_action = Action.SELL
        exit_quantity = -50
        exit_price = 45
        
        # test
        trade_pnl = self.dummy_broker._calculate_trade_pnl(self.dummy_broker.positions[contract],exit_price, exit_quantity)
        
        # expected
        expected_pnl =  (exit_price - entry_price) * price_multiplier * exit_quantity * quantity_multiplier * -1
        
        # validate
        self.assertEqual(trade_pnl, expected_pnl)

    def test_update_account_futures_new_position(self):
        # Variables
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(
                                                    avg_cost=entry_price*price_multiplier*quantity_multiplier,  
                                                    quantity=entry_quantity, 
                                                    action=entry_action,
                                                    price_multiplier=price_multiplier,
                                                    quantity_multiplier=quantity_multiplier,
                                                    unrealizedPnl = 0 )
        
        # Test
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry
    
    def test_update_account_futures_full_exit(self):
        # Entry Variables 
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price*price_multiplier*quantity_multiplier,  
                                                                quantity=entry_quantity, 
                                                                action=entry_action,
                                                                price_multiplier=price_multiplier,
                                                                quantity_multiplier=quantity_multiplier,
                                                                unrealizedPnl = 0)
        
        # Entry
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry

        # Exit Variables
        exit_action = Action.COVER
        exit_quantity = 100
        exit_price = 45
        fees = 70
        unrealized_pnl = 1000
        
        self.dummy_broker.positions[contract]['unrealizedPnL'] = 1000
        self.dummy_broker.account['FullAvailableFunds'] += unrealized_pnl
        capital = self.dummy_broker.account['FullAvailableFunds'] 

        # Test
        self.dummy_broker._update_account_futures(contract, exit_action, exit_quantity, exit_price, fees)

        # Validation
        expected_funds = (capital - fees) + ((exit_price - entry_price) * price_multiplier * exit_quantity * quantity_multiplier * -1) - unrealized_pnl
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted for pnl and fees on exit
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], 0) # Position exited margin should be fully removed
    
    def test_update_account_futures_add_to_position(self):
        # First Entry Variables 
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70
        # entry_value = entry_price * quantity * multiplier
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                                                quantity=entry_quantity, 
                                                                action=entry_action,
                                                                price_multiplier=price_multiplier,
                                                                quantity_multiplier=quantity_multiplier,
                                                                unrealizedPnl = 0)
        
        # Entry
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry

        # Additional Entry
        add_action = Action.SHORT
        add_quantity = -10
        add_price = 45
        fees = 70
        
        unrealized_pnl = 1000
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        current_margin = self.dummy_broker.account['FullInitMarginReq']

        # Test
        self.dummy_broker._update_account_futures(contract, add_action, add_quantity, add_price, fees)
        
        # Validation
        expected_funds = capital - fees
        expected_margin = current_margin + self.valid_symbols_map[contract.symbol].initialMargin * abs(add_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted for pnl and fees on exit
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # Position exited margin should be fully removed

    def test_update_account_futures_reduce_a_position_postive_pnl(self):
        # Entry Variables 
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                                                quantity=entry_quantity, 
                                                                action=entry_action,
                                                                price_multiplier=price_multiplier,
                                                                quantity_multiplier=quantity_multiplier, 
                                                                unrealizedPnl = 0)
        
        # Entry
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry

        # Exit Variables
        exit_action = Action.LONG
        exit_quantity = 50
        exit_price = 45
        fees = 70
        unrealized_pnl = 1000
        
        self.dummy_broker.positions[contract]['unrealizedPnL'] = 1000
        self.dummy_broker.account['FullAvailableFunds'] += unrealized_pnl
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        margin = self.dummy_broker.account['FullInitMarginReq']

        # Test
        self.dummy_broker._update_account_futures(contract, exit_action, exit_quantity, exit_price, fees)

        # Validation
        accounted_for_pnl = (unrealized_pnl/abs(self.dummy_broker.positions[contract]['quantity'])) * exit_quantity
        expected_funds = (capital - fees) + ((exit_price - entry_price) * price_multiplier * exit_quantity * quantity_multiplier * -1) - accounted_for_pnl
        expected_margin = margin - (abs(exit_quantity) *  self.valid_symbols_map[contract.symbol].initialMargin) 
        expected_unrealized_pnl = unrealized_pnl - accounted_for_pnl
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted for pnl and fees on exit
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # Position exited margin should be fully removed
        self.assertEqual(self.dummy_broker.positions[contract]['unrealizedPnL'], expected_unrealized_pnl)

    def test_update_account_futures_reduce_a_position_negative_pnl(self):
        # Entry Variables 
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price*price_multiplier*quantity_multiplier,
                                                                quantity=entry_quantity, 
                                                                action=entry_action,
                                                                price_multiplier=price_multiplier,
                                                                quantity_multiplier=quantity_multiplier,   
                                                                unrealizedPnl = 0)
        
        # Entry
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry

        # Exit Variables
        exit_action = Action.LONG
        exit_quantity = 50
        exit_price = 55
        fees = 70
        unrealized_pnl = - 1000
        
        self.dummy_broker.positions[contract]['unrealizedPnL'] = unrealized_pnl
        self.dummy_broker.account['FullAvailableFunds'] += unrealized_pnl
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        margin = self.dummy_broker.account['FullInitMarginReq']

        # Test
        self.dummy_broker._update_account_futures(contract, exit_action, exit_quantity, exit_price, fees)

        # Validation
        accounted_for_pnl = (unrealized_pnl/abs(self.dummy_broker.positions[contract]['quantity'])) * exit_quantity
        expected_funds = (capital - fees) + ((exit_price - entry_price) * price_multiplier * exit_quantity *quantity_multiplier * -1) - accounted_for_pnl
        expected_margin = margin - (abs(exit_quantity) *  self.valid_symbols_map[contract.symbol].initialMargin) 
        expected_unrealized_pnl = unrealized_pnl - accounted_for_pnl
    
        self.assertAlmostEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted for pnl and fees on exit
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # Position exited margin should be fully removed
        self.assertEqual(self.dummy_broker.positions[contract]['unrealizedPnL'], expected_unrealized_pnl)

    def test_update_account_futures_flip_a_position(self):
        # Entry Variables 
        contract = Contract()
        contract.symbol = 'HEJ4'
        ticker = contract.symbol
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price*price_multiplier*quantity_multiplier, 
                                                                quantity=entry_quantity, 
                                                                action=entry_action,
                                                                price_multiplier=price_multiplier,
                                                                quantity_multiplier=quantity_multiplier,   
                                                                unrealizedPnl = 0)
        
        # Entry
        self.dummy_broker._update_account_futures(contract, entry_action, entry_quantity,entry_price, fees)

        # Validation
        expected_funds = capital - fees
        expected_margin = self.valid_symbols_map[contract.symbol].initialMargin * abs(entry_quantity)
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only fees, on entry of futures
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # margin increased for entry

        # Exit Variables
        exit_action = Action.LONG
        exit_quantity = 200
        exit_price = 55
        fees = 70
        unrealized_pnl = - 1000
        
        self.dummy_broker.positions[contract]['unrealizedPnL'] = unrealized_pnl
        self.dummy_broker.account['FullAvailableFunds'] += unrealized_pnl
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        margin = self.dummy_broker.account['FullInitMarginReq']

        # Test
        self.dummy_broker._update_account_futures(contract, exit_action, exit_quantity, exit_price, fees)

        # Validation
        expected_funds = (capital - fees) + ((exit_price - entry_price) * price_multiplier * exit_quantity *  quantity_multiplier * -1) - unrealized_pnl
        margin -= (abs(entry_quantity) *  self.valid_symbols_map[contract.symbol].initialMargin)
        margin += (abs(exit_quantity) - abs(entry_quantity) *  self.valid_symbols_map[contract.symbol].initialMargin)
        
    
        self.assertAlmostEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted for pnl and fees on exit
        self.assertEqual(self.dummy_broker.account['FullInitMarginReq'], expected_margin) # Position exited margin should be fully removed
        self.assertEqual(self.dummy_broker.positions[contract]['unrealizedPnL'], 0)

    def test_update_account_equities_LONG(self):
        # Variables
        contract = Contract()
        contract.symbol = 'AAPL'
        entry_action = Action.LONG
        entry_quantity = 100
        entry_price=50
        fees = 70

        self.dummy_broker.account['FullAvailableFunds'] = 10000
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price)
        
        # Entry
        self.dummy_broker._update_account_equities(contract, entry_action, entry_quantity, entry_price, fees)
        
        # Validation
        expected_funds = capital - fees - (entry_price * abs(entry_quantity))
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only captal to enter

        # Exit
        exit_action = Action.SELL
        exit_quantity = -100
        exit_price = 80
        fees = 70
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        
        self.dummy_broker._update_account_equities(contract, exit_action, exit_quantity, exit_price, fees)

        expected_funds = (capital - fees) + (exit_price * abs(exit_quantity))
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted by proceeds of exit

    def test_update_account_equities_SHORT(self):
        # Variables
        contract = Contract()
        contract.symbol = 'AAPL'
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70
        
        self.dummy_broker.account['FullAvailableFunds'] = 10000
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        self.dummy_broker.positions[contract] = PositionDetails(avg_cost=entry_price)
        
        # Entry
        self.dummy_broker._update_account_equities(contract, entry_action, entry_quantity, entry_price, fees)

        # Validation
        expected_funds = capital - fees + (entry_price * abs(entry_quantity))
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital should be adjust by only captal to enter

        # Exit
        exit_action = Action.COVER
        exit_quantity = 100
        exit_price = 80
        fees = 70
        capital = self.dummy_broker.account['FullAvailableFunds'] 
        
        # Test
        self.dummy_broker._update_account_equities(contract, exit_action, exit_quantity, exit_price, fees)

        # Validation
        expected_funds = (capital - fees) - (exit_price * abs(exit_quantity))
        self.assertEqual(self.dummy_broker.account['FullAvailableFunds'], expected_funds) # capital shoudl be adjusted by proceeds of exit

    def test_update_positions_NEW(self):
        # Variables
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        action = Action.SHORT
        quantity = -100
        fill_price = 90

        valid_position = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(fill_price * price_multiplier* quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,      
                initial_margin = self.valid_symbols_map[ticker].initialMargin, 
                unrealizedPnL=0
        )
        # test
        self.dummy_broker._update_positions(contract,action,quantity, fill_price)

        # validate
        self.assertEqual(self.dummy_broker.positions[contract], valid_position)

    def test_update_positions_full_exit_OLD(self):
        ticker = 'HEJ4'
        contract = Contract()
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        contract.symbol = ticker
        
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price = 90
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= entry_quantity,
                avg_cost=round(entry_price* price_multiplier * quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,    
                initial_margin = self.valid_symbols_map[ticker].initialMargin, 
                unrealizedPnL=0
        )
        
        self.dummy_broker.positions[contract] = valid_position

        exit_action = Action.COVER
        exit_quantity = 100
        exit_price = 90
        
        # test
        self.dummy_broker._update_positions(contract,exit_action,exit_quantity, exit_price)
        
        # validate
        self.assertEqual(self.dummy_broker.positions, {}) # position should be removed

    def test_update_positions_add_to_OLD(self):
        # Variables
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        
        old_action = Action.SHORT
        old_quantity = -100
        old_price = 90
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= old_quantity,
                avg_cost=round(old_price * price_multiplier * quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,  
                initial_margin = self.valid_symbols_map[ticker].initialMargin,
                unrealizedPnL=0
        )
        self.dummy_broker.positions[contract] = valid_position

        new_action = Action.SHORT
        new_quantity = -10
        new_price = 70
        # Test
        self.dummy_broker._update_positions(contract, new_action, new_quantity, new_price)

        # Validation
        self.assertEqual(self.dummy_broker.positions[contract]['action'], new_action.to_broker_standard())
        self.assertEqual(self.dummy_broker.positions[contract]['quantity'], new_quantity + old_quantity)
        
        old_cost = old_quantity * old_price * price_multiplier * quantity_multiplier
        new_cost = new_quantity * new_price * price_multiplier * quantity_multiplier
        self.assertEqual(self.dummy_broker.positions[contract]['avg_cost'], (new_cost + old_cost)/(new_quantity+old_quantity) )

    def test_update_positions_reverse_OLD(self):
        # Variables
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        
        old_action = Action.SHORT
        old_quantity = -100
        old_price = 90
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= old_quantity,
                avg_cost=round(old_price * price_multiplier * quantity_multiplier,4),
                quantity_multiplier= quantity_multiplier,  
                price_multiplier= price_multiplier,      
                initial_margin = self.valid_symbols_map[ticker].initialMargin,
                unrealizedPnL=0
        )
        self.dummy_broker.positions[contract] = valid_position

        new_action = Action.LONG
        new_quantity = 200
        new_price = 70

        # Test
        self.dummy_broker._update_positions(contract, new_action, new_quantity, new_price)

        # validate
        self.assertEqual(self.dummy_broker.positions[contract]['action'], 'BUY')
        self.assertEqual(self.dummy_broker.positions[contract]['quantity'], new_quantity + old_quantity)
        self.assertEqual(self.dummy_broker.positions[contract]['avg_cost'], new_price)
        self.assertEqual(self.dummy_broker.positions[contract]['total_cost'], new_price * (new_quantity + old_quantity))

    def test_position_value_futures(self):
        # Variables
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        
        action = Action.SHORT
        quantity = -10
        entry_price = 50
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(entry_price*price_multiplier*quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,  
                initial_margin = self.valid_symbols_map[ticker].initialMargin,
                unrealizedPnL=0
        )
        self.dummy_broker.positions[contract] = valid_position

        current_price = 40

        # Test
        position_value = self.dummy_broker._future_position_value(valid_position,current_price)
        
        # validate
        expected_value = (current_price - entry_price)  * price_multiplier * quantity * quantity_multiplier
        self.assertEqual(position_value, expected_value)

    def test_position_value_equities(self):
        # Variables
        ticker = 'AAPL'
        contract = Contract()
        contract.symbol = ticker
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier

        action = Action.SHORT
        quantity = -10
        entry_price = 50
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(entry_price * price_multiplier * quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,     
                initial_margin = self.valid_symbols_map[ticker].initialMargin)
        self.dummy_broker.positions[contract] = valid_position

        current_price = 40
        
        # Test
        position_value = self.dummy_broker._equity_position_value(valid_position,current_price)
        
        # validate
        expected_value = current_price * price_multiplier * quantity * quantity_multiplier
        self.assertEqual(position_value, expected_value)

    def test_portfolio_value(self):
        # Position 1
        ticker1 = 'AAPL'
        aapl_contract = Contract()
        aapl_contract.symbol = ticker1
        aapl_contract.secType = 'STK'
        action = Action.LONG
        quantity = 10
        entry_price = 50
        quantity_multiplier= self.valid_symbols_map[ticker1].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker1].price_multiplier
        valid_position1 = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(entry_price*price_multiplier * quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker1].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker1].price_multiplier,    
                initial_margin = self.valid_symbols_map[ticker1].initialMargin)
        self.dummy_broker.positions[aapl_contract] = valid_position1
        
        # Position 2
        ticker2 = 'HEJ4'
        he_contract = Contract()
        he_contract.symbol = ticker2
        he_contract.secType = 'FUT'
        action = Action.SHORT
        quantity = -10
        entry_price = 50        
        quantity_multiplier2= self.valid_symbols_map[ticker2].quantity_multiplier
        price_multiplier2= self.valid_symbols_map[ticker2].price_multiplier
        valid_position2 = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(entry_price * price_multiplier2 * quantity_multiplier2,4),
                quantity_multiplier= self.valid_symbols_map[ticker2].quantity_multiplier,  
                price_multiplier= self.valid_symbols_map[ticker2].price_multiplier,        
                initial_margin = self.valid_symbols_map[ticker2].initialMargin
        )
        self.dummy_broker.positions[he_contract] = valid_position2

        # Test 
        self.mock_order_book.current_prices.return_value = {ticker1: 90.9, ticker2: 9.9}
        with patch.object(self.dummy_broker, '_future_position_value', return_value = 500) as mock_future_method:
            with patch.object(self.dummy_broker, '_equity_position_value', return_value = 500) as mock_equity_method:
                position_value = self.dummy_broker._calculate_portfolio_value()
                self.assertEqual(position_value, 500 * 2) # 2 positions with mock postiosn values of 500

                # Equity
                self.assertTrue(mock_equity_method.called) # ensure _postion_value was called
                called_w_args = mock_equity_method.call_args[0] # get arguements for last _position_value call
                self.assertEqual(called_w_args[0], valid_position1) # check postion arguement aligns
                self.assertEqual(called_w_args[1], self.mock_order_book.current_prices.return_value[ticker1]) # check current_price arguement aligns

                # Future
                self.assertTrue(mock_future_method.called) # ensure _postion_value was called
                called_w_args = mock_future_method.call_args[0] # get arguements for last _position_value call
                self.assertEqual(called_w_args[0], valid_position2) # check postion arguement aligns
                self.assertEqual(called_w_args[1], self.mock_order_book.current_prices.return_value[ticker2]) # check current_price arguement aligns


        # self.assertEqual(position_value, expected_value)

    def test_update_equity_value(self):
        self.mock_order_book.last_updated = 1651500000
        portfolio_value = 1000000

        with patch.object(self.dummy_broker, '_calculate_portfolio_value', return_value = portfolio_value) as mock_method:
            # test
            self.dummy_broker._update_account_equity_value()
            
            # validate
            self.assertTrue(mock_method)
            expected_value = self.dummy_broker.account['FullAvailableFunds'] + portfolio_value
            self.assertEqual(self.dummy_broker.account['Timestamp'],self.mock_order_book.last_updated)
            self.assertEqual(self.dummy_broker.account['NetLiquidation'], expected_value)

    def test_update_trades(self):
        timestamp = 1651500000 
        trade_id = 1 
        leg_id = 2 
        contract = Contract()
        contract.symbol = 'AAPL'
        ticker = contract.symbol
        quantity = -10
        action =  Action.LONG
        fill_price = 9.9 
        fees = 90.9
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier

        valid_trade = ExecutionDetails(
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            symbol = contract.symbol,
            quantity = round(quantity,4),
            price = fill_price,
            cost = round(fill_price*price_multiplier * quantity * quantity_multiplier, 2),
            action = action.value,
            fees = round(fees,4)
        )
        
        # test
        trade = self.dummy_broker._update_trades(timestamp, trade_id, leg_id, contract, quantity, action, fill_price, fees)
        
        # validate
        self.assertEqual(self.dummy_broker.last_trade[contract],valid_trade)

    def test_set_execution(self):
        timestamp = np.uint64(1651500000)
        contract = Contract()
        contract.symbol = 'AAPL'
        action =  Action.LONG
        valid_trade_details = ExecutionDetails(
            timestamp = timestamp,
            trade_id = 1,
            leg_id = 2,
            symbol = contract.symbol,
            quantity = round(10, 4),
            price = 90.9,
            cost = round(90.9 * 10, 2),
            action = action.value,
            fees = round(90.9 ,4)
        )
        # test
        self.dummy_broker._set_execution(timestamp,valid_trade_details, action, contract)
        
        # validate
        # Assert that event_queue.put() was called
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.")

        # Get the argument with which event_queue.put was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0]
        self.assertIsInstance(called_with_arg, ExecutionEvent, "The argument is not an instance of ExecutionEvent")

    def test_mark_to_market(self):
        # Position
        ticker = 'HEJ4'
        he_contract = Contract()
        he_contract.symbol = ticker
        action = Action.SHORT
        quantity = -10
        entry_price = 50
        quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier
        price_multiplier= self.valid_symbols_map[ticker].price_multiplier
        unrealizedpnl = 500

        valid_position = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round(entry_price*price_multiplier * quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker].quantity_multiplier,
                price_multiplier= self.valid_symbols_map[ticker].price_multiplier,      
                initial_margin = self.valid_symbols_map[ticker].initialMargin,
                unrealizedPnL=500
        )
        self.dummy_broker.positions[he_contract] = valid_position
        capital = self.dummy_broker.account['FullAvailableFunds']

        self.mock_order_book.current_prices.return_value = {ticker: 100}
        pnl = 1000
        with patch.object(self.dummy_broker, '_future_position_value', return_value = pnl) as mock_position_value:
            # test
            self.dummy_broker.mark_to_market()
            
            # validate
            self.assertEqual(self.dummy_broker.positions[he_contract]['unrealizedPnL'], pnl)
            self.assertEqual(self.dummy_broker.account['FullAvailableFunds'],capital + (pnl - unrealizedpnl))

    def test_check_margin_call(self):
        # Margin Call
        self.dummy_broker.account['FullAvailableFunds'] = 100 
        self.dummy_broker.account['FullInitMarginReq'] = 200
        self.assertTrue(self.dummy_broker.check_margin_call() == True)

        # No Margin Call
        self.dummy_broker.account['FullAvailableFunds'] = 2000
        self.dummy_broker.account['FullInitMarginReq'] = 200
        self.assertTrue(self.dummy_broker.check_margin_call() == False)

    def test_liquidate_positions(self):
        # Position 1
        ticker1 = 'AAPL'
        aapl_contract = Contract()
        aapl_contract.symbol = ticker1
        aapl_contract.secType = 'STK'
        aapl_action = Action.LONG
        aapl_quantity = 10
        aapl_entry_price = 50
        aapl_quantity_multiplier= self.valid_symbols_map[ticker1].quantity_multiplier
        aapl_price_multiplier= self.valid_symbols_map[ticker1].price_multiplier
        valid_position1 = PositionDetails(
                action='BUY',
                quantity= aapl_quantity,
                avg_cost=round(aapl_entry_price * aapl_price_multiplier * aapl_quantity_multiplier,4),
                quantity_multiplier=self.valid_symbols_map[ticker1].quantity_multiplier,
                price_multiplier= self.valid_symbols_map[ticker1].price_multiplier,
                initial_margin = self.valid_symbols_map[ticker1].initialMargin)
        self.dummy_broker.positions[aapl_contract] = valid_position1
        
        valid_trade_appl = ExecutionDetails(
                timestamp= 165000000,
                trade_id= 1,
                leg_id=1,
                symbol= aapl_contract.symbol,
                quantity= round(aapl_quantity,4),
                price= aapl_entry_price,
                cost= round(aapl_entry_price *aapl_price_multiplier * aapl_quantity * aapl_quantity_multiplier, 2),
                action= aapl_action.value,
                fees= 70 # because not actually a trade
            )
        self.dummy_broker.last_trade[aapl_contract] = valid_trade_appl
        
        # Position 2
        ticker2 = 'HEJ4'
        he_contract = Contract()
        he_contract.symbol = ticker2
        he_contract.secType = 'FUT'
        he_action = Action.SHORT
        he_quantity = -10
        he_entry_price = 50
        he_quantity_multiplier= self.valid_symbols_map[ticker2].quantity_multiplier
        he_price_multiplier= self.valid_symbols_map[ticker2].price_multiplier
        valid_position2 = PositionDetails(
                action='SELL',
                quantity= he_quantity,
                avg_cost=round(he_entry_price * he_price_multiplier* he_quantity_multiplier,4),
                quantity_multiplier= self.valid_symbols_map[ticker2].quantity_multiplier,
                price_multiplier= self.valid_symbols_map[ticker2].price_multiplier,  
                initial_margin = self.valid_symbols_map[ticker2].initialMargin
        )
        self.dummy_broker.positions[he_contract] = valid_position2
        
        valid_trade_he = ExecutionDetails(
                timestamp= 165000000,
                trade_id= 2,
                leg_id=2,
                symbol= he_contract.symbol,
                quantity= round(he_quantity,4),
                price= he_entry_price,
                cost= round(he_entry_price * he_price_multiplier * he_quantity * he_quantity_multiplier, 2),
                action= he_action.value,
                fees= 70 # because not actually a trade
        )
        self.dummy_broker.last_trade[he_contract] = valid_trade_he

        self.mock_order_book.book = {ticker1:Mock(timestamp= 1655000000), ticker2:Mock(timestamp= 1655000000) }

        with patch.object(self.dummy_broker, '_fill_price', return_value = 100) as mock_fill_price:
            # test
            self.dummy_broker.liquidate_positions()
            
            # validate
            self.assertEqual(self.dummy_broker.last_trade[aapl_contract], ExecutionDetails(
                                                                            timestamp= 1655000000,
                                                                            trade_id= 1,
                                                                            leg_id=1,
                                                                            symbol= aapl_contract.symbol,
                                                                            quantity= round(aapl_quantity * -1,4),
                                                                            price= mock_fill_price.return_value,
                                                                            cost= round(mock_fill_price.return_value * aapl_quantity * -1 * aapl_price_multiplier  * aapl_quantity_multiplier, 2),
                                                                            action=Action.SELL.value,
                                                                            fees= 0.0 # because not actually a trade
                                                                        ) )
            
            self.assertEqual(self.dummy_broker.last_trade[he_contract], ExecutionDetails(
                                                                timestamp= 1655000000,
                                                                trade_id= 2,
                                                                leg_id=2,
                                                                symbol= he_contract.symbol,
                                                                quantity= round(he_quantity * -1,4),
                                                                price= mock_fill_price.return_value,
                                                                cost= round(mock_fill_price.return_value * he_quantity * -1 * he_price_multiplier * he_quantity_multiplier , 2),
                                                                action=Action.COVER.value,
                                                                fees= 0.0 # because not actually a trade
                                                            ) )
   
    def test_update_account_future(self):
        # Variables
        contract = Contract()
        contract.symbol = 'HEJ4'
        entry_action = Action.SHORT
        entry_quantity = -100
        entry_price=50
        fees = 70

        with ExitStack() as stack:
            mock_update_account = stack.enter_context(patch.object(self.dummy_broker,'_update_account_futures'))
            mock_update_positions = stack.enter_context(patch.object(self.dummy_broker,'_update_positions'))
            mock_update_account_equity_value = stack.enter_context(patch.object(self.dummy_broker,'_update_account_equity_value'))
            # test 
            self.dummy_broker._update_account(contract, entry_action, entry_quantity, entry_price, fees)
            
            # validate
            self.assertTrue(mock_update_account_equity_value.called)
            self.assertTrue(mock_update_account.called)
            self.assertTrue(mock_update_account_equity_value.called)

    def test_update_account_equity(self):
        # Variables
        contract = Contract()
        contract.symbol = 'AAPL'
        entry_action = Action.LONG
        entry_quantity = 100
        entry_price=50
        fees = 70

        with ExitStack() as stack:
            mock_update_account = stack.enter_context(patch.object(self.dummy_broker,'_update_account_equities'))
            mock_update_positions = stack.enter_context(patch.object(self.dummy_broker,'_update_positions'))
            mock_update_account_equity_value = stack.enter_context(patch.object(self.dummy_broker,'_update_account_equity_value'))
            
            # test
            self.dummy_broker._update_account(contract, entry_action, entry_quantity, entry_price, fees)
            
            # validate
            self.assertTrue(mock_update_account_equity_value.called)
            self.assertTrue(mock_update_account.called)
            self.assertTrue(mock_update_account_equity_value.called)

    def test_place_order(self):
        timestamp = 1655000000 
        trade_id = 1 
        leg_id = 1 
        action = Action.LONG 
        contract = Contract() 
        order = MarketOrder(action, quantity = 10)


        with ExitStack() as stack:
            mock_fill_price = stack.enter_context(patch.object(self.dummy_broker,'_fill_price'))
            mock_calculate_commission_fees= stack.enter_context(patch.object(self.dummy_broker,'_calculate_commission_fees'))
            mock_update_account = stack.enter_context(patch.object(self.dummy_broker,'_update_account'))
            mock_update_trades = stack.enter_context(patch.object(self.dummy_broker,'_update_trades'))
            mock_set_execution = stack.enter_context(patch.object(self.dummy_broker,'_set_execution'))
            
            # test
            self.dummy_broker.placeOrder(timestamp, trade_id, leg_id, action, contract, order)

            # validate
            self.assertTrue(mock_fill_price.called)
            self.assertTrue(mock_update_account.called)
            self.assertTrue(mock_calculate_commission_fees.called)
            self.assertTrue(mock_update_trades.called)
            self.assertTrue(mock_set_execution.called)

    # Type and Constraint Validation
    def test_slippage_adjust_price(self):
        tick_size = 1
        current_price = 10
        action = 'LONG'

        with self.assertRaisesRegex(ValueError,"'action' must be of type Action enum."):
            self.dummy_broker._slippage_adjust_price(tick_size, current_price, action)

    def test_calculate_commission_fees_symbol_missing(self):
        contract = Contract()
        contract.symbol = 'invalid'
        quantity = 90
        
        # test
        commission = self.dummy_broker._calculate_commission_fees(contract, quantity)
        
        # validate
        self.assertEqual(commission, 0)
        self.assertTrue(self.mock_logger.error.called, "Logger did not log error")
        
    # Integration 

if __name__ =="__main__":
    unittest.main()