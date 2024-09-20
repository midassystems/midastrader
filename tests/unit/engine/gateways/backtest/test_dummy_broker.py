import unittest
import numpy as np
from contextlib import ExitStack
from midas.shared.trade import Trade
from unittest.mock import Mock, patch
from midas.shared.account import Account
from midas.engine.events import ExecutionEvent
from midas.shared.orders import Action, MarketOrder
from midas.engine.gateways.backtest.dummy_broker import DummyBroker
from midas.shared.symbol import Future, Equity, Currency,Venue, Future, ContractUnits, Industry
from midas.shared.positions import FuturePosition, EquityPosition, OptionPosition, position_factory


class TestDummyClient(unittest.TestCase):
    def setUp(self) -> None:
        # Mock object
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()
        self.mock_logger = Mock()

        # Test data
        self.capital = 100000
        self.symbols_map = {
                            'HEJ4' : Future(ticker = "HEJ4",
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
                                            shares_outstanding=1937476363)
                            }

        # Dummybroker instance
        self.dummy_broker = DummyBroker(self.symbols_map, self.mock_event_queue, self.mock_order_book, self.capital, self.mock_logger)

    def test_place_order(self):
        # Mock order data
        timestamp = 1655000000 
        trade_id = 1 
        leg_id = 1 
        action = Action.LONG 
        symbol = self.symbols_map["HEJ4"]
        contract = symbol.contract

        # Mock methods
        self.mock_order_book.current_price.return_value = 10
        symbol.commission_fees = Mock(return_value=10)
        symbol.slippage_price = Mock(return_value=9)
        order = MarketOrder(action, quantity = 10)

        with ExitStack() as stack:
            mock_update_positions = stack.enter_context(patch.object(self.dummy_broker,'_update_positions'))
            mock_update_account = stack.enter_context(patch.object(self.dummy_broker,'_update_account'))
            mock_update_trades = stack.enter_context(patch.object(self.dummy_broker,'_update_trades'))
            mock_set_execution = stack.enter_context(patch.object(self.dummy_broker,'_set_execution'))
            
            # Test
            self.dummy_broker.placeOrder(timestamp, trade_id, leg_id, action,contract, order)

            # Validate
            self.assertTrue(symbol.commission_fees.called)
            self.assertTrue(symbol.slippage_price.called)
            self.assertTrue(mock_update_positions.called)
            self.assertTrue(mock_update_account.called)
            self.assertTrue(mock_update_trades.called)
            self.assertTrue(mock_set_execution.called)

    def test_update_positions_update(self):
        symbol = self.symbols_map["AAPL"]
        contract = symbol.contract

        # Old Position
        old_position = EquityPosition(
                action = 'BUY',
                avg_price = 10,
                quantity = 100,
                quantity_multiplier = 1,
                price_multiplier = 1,
                market_price = 20,

        )
        self.dummy_broker.positions[contract] = old_position

        # New order
        action = Action.SELL
        quantity=  -50
        fill_price = 25
        
        # Test
        self.dummy_broker._update_positions(symbol, action, quantity, fill_price)

        # Expected
        full_available_funds_available = 25 * abs(50) + self.capital

        # Validate
        self.assertEqual(self.dummy_broker.account.full_available_funds, full_available_funds_available)
        
    def test_update_positions_new(self):
        symbol = self.symbols_map["AAPL"]

        # New order
        action = Action.SELL
        quantity=  -50
        fill_price = 25
        
        # Test
        self.dummy_broker._update_positions(symbol, action, quantity, fill_price)

        # Expected
        full_available_funds_available =  fill_price * abs(quantity) + self.capital

        # Validate
        self.assertEqual(self.dummy_broker.account.full_available_funds, full_available_funds_available)

    def test_update_account(self):
        # Position1 
        hogs_position = FuturePosition(
                action = 'BUY',
                avg_price = 10,
                quantity = 80,
                quantity_multiplier = 400000,
                price_multiplier = 0.01,
                market_price = 10,
                initial_margin= 5000
        )
        hogs_contract = self.symbols_map['HEJ4'].contract
        self.dummy_broker.positions[hogs_contract] = hogs_position

        # Position2
        aapl_position = EquityPosition(
                action = 'BUY',
                avg_price = 10,
                quantity = 100,
                quantity_multiplier = 1,
                price_multiplier = 1,
                market_price = 10,

        )
        aapl_contract = self.symbols_map['AAPL'].contract
        self.dummy_broker.positions[aapl_contract] = aapl_position

        # Mock orderbook responses
        current_price = 90
        self.mock_order_book.current_price.return_value = 90
        self.mock_order_book.last_updated = np.uint64(1777700000000000)

        # Test
        self.dummy_broker._update_account()

        # Expected
        hogs_unrealized_pnl = (current_price - hogs_position.avg_price) * hogs_position.quantity * hogs_position.quantity_multiplier * hogs_position.price_multiplier
        hogs_liquidation_value =  (hogs_position.quantity * hogs_position.initial_margin) + hogs_unrealized_pnl
        hogs_margin_required = hogs_position.initial_margin * hogs_position.quantity

        aapl_unrealized_pnl = (current_price - aapl_position.avg_price) * aapl_position.quantity 
        aapl_liquidation_value = (current_price * aapl_position.quantity)
        aapl_margin_required = 0

        expected_account = Account(
                            timestamp= np.uint64(1777700000000000), 
                            full_available_funds=self.capital,
                            net_liquidation= hogs_liquidation_value + aapl_liquidation_value + self.capital,
                            full_init_margin_req= hogs_margin_required + aapl_margin_required, 
                            unrealized_pnl= hogs_unrealized_pnl + aapl_unrealized_pnl,
        )

        # Validate
        self.assertEqual(self.dummy_broker.account, expected_account)

    def test_update_trades(self):
        timestamp = np.uint64(1651500000)
        trade_id = 1 
        leg_id = 2 
        ticker = "AAPL"
        symbol = self.symbols_map[ticker]
        quantity = -10
        action =  Action.LONG
        fill_price = 9.9 
        fees = 90.9

        # Exception
        expected_trade = Trade(
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            ticker = symbol.ticker,
            quantity = round(quantity,4),
            avg_price = fill_price,
            trade_value = round(fill_price * quantity, 2),
            trade_cost = round(abs(quantity) * fill_price, 2),
            action = action.value,
            fees = round(fees,4)
        )
        
        # Test
        self.dummy_broker._update_trades(timestamp, trade_id, leg_id, symbol, quantity, action, fill_price, fees)

        # Validate
        self.assertEqual(self.dummy_broker.last_trades[symbol.contract], expected_trade)

    def test_set_execution(self):
        timestamp = np.uint64(1651500000)
        trade_id = 1 
        leg_id = 2 
        ticker = "AAPL"
        symbol = self.symbols_map[ticker]
        quantity = -10
        action =  Action.LONG
        fill_price = 9.9 
        fees = 90.9

        trade = Trade(
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            ticker = symbol.ticker,
            quantity = round(quantity,4),
            avg_price = fill_price,
            trade_value = round(fill_price * symbol.price_multiplier * quantity * symbol.quantity_multiplier, 2),
            trade_cost = round(fill_price * symbol.price_multiplier * quantity * symbol.quantity_multiplier, 2),
            action = action.value,
            fees = round(fees,4)
        )

        # Test
        self.dummy_broker._set_execution(timestamp,trade, action, symbol)
        
        # Validate
        # Assert that event_queue.put() was called
        self.assertTrue(self.mock_event_queue.put.called, "The event_queue.put() method was not called.")

        # Get the argument with which event_queue.put was called
        called_with_arg = self.mock_event_queue.put.call_args[0][0]
        self.assertIsInstance(called_with_arg, ExecutionEvent, "The argument is not an instance of ExecutionEvent")

    def test_mark_to_market(self):
        self.dummy_broker._update_account = Mock()

        # Test
        self.dummy_broker.mark_to_market()

        # Validate
        self.dummy_broker._update_account.assert_called()
        self.mock_logger.info.assert_called()

    def test_check_margin_call(self):
        # Margin Call
        self.dummy_broker.account.full_available_funds = 100 
        self.dummy_broker.account.full_init_margin_req = 2000
        
        # Test
        self.dummy_broker.check_margin_call()
        
        # Validate
        self.mock_logger.info.assert_called_with("Margin call triggered.")

    def test_check_margin_call_no_call(self):
        # No Margin Call
        self.dummy_broker.account.full_available_funds = 2000
        self.dummy_broker.account.full_init_margin_req = 200
        
        # Test
        self.dummy_broker.check_margin_call()

        # Validate
        self.mock_logger.info.assert_not_called()

    def test_liquidate_positions(self):
        # Position1 
        hogs_position = FuturePosition(
                action = 'BUY',
                avg_price = 10,
                quantity = 80,
                quantity_multiplier = 40000,
                price_multiplier = 0.01,
                market_price = 10,
                initial_margin= 4564.17
        )
        hogs_contract = self.symbols_map['HEJ4'].contract
        self.dummy_broker.positions[hogs_contract] = hogs_position

        hogs_trade = Trade(
            timestamp=np.uint64(165000000),
            trade_id=1,
            leg_id=1,
            ticker=hogs_contract.symbol,
            quantity=round(hogs_position.quantity, 4),
            avg_price= hogs_position.avg_price,
            trade_value=round(hogs_position.avg_price * hogs_position.price_multiplier * hogs_position.quantity_multiplier * hogs_position.quantity, 2),
            trade_cost = hogs_position.initial_margin * hogs_position.quantity,
            action= hogs_position.action,
            fees= 70
        )
        self.dummy_broker.last_trades[hogs_contract] = hogs_trade

        # Position2
        aapl_position = EquityPosition(
                action = 'BUY',
                avg_price = 10,
                quantity = 100,
                quantity_multiplier = 1,
                price_multiplier = 1,
                market_price = 10,

        )
        aapl_contract = self.symbols_map['AAPL'].contract
        self.dummy_broker.positions[aapl_contract] = aapl_position
        
        aapl_trade = Trade(
            timestamp=np.uint64(165000000),
            trade_id=2,
            leg_id=2,
            ticker=aapl_contract.symbol,
            quantity=round(aapl_position.quantity,4),
            avg_price=aapl_position.avg_price,
            trade_value=round(aapl_position.avg_price * aapl_position.quantity, 2),
            trade_cost=round(aapl_position.avg_price * aapl_position.quantity, 2),
            action=aapl_position.action,
            fees=70 
        )
        self.dummy_broker.last_trades[aapl_contract] = aapl_trade
        
        # Mock order book response
        current_price = 90
        self.mock_order_book.current_price.return_value = current_price
        self.mock_order_book.last_updated = np.uint64(17777000000000)
        # Test
        self.dummy_broker.liquidate_positions()

        # Expected 
        hogs_trade_liquidated = Trade(
                timestamp=np.uint64(17777000000000),
                trade_id=1,
                leg_id=1,
                ticker=hogs_contract.symbol,
                quantity=round(hogs_position.quantity * -1, 4),
                avg_price= current_price,
                trade_value=round((current_price * hogs_position.quantity * hogs_position.quantity_multiplier * hogs_position.price_multiplier), 2),
                trade_cost= hogs_position.initial_margin * hogs_position.quantity ,
                action= Action.SELL.value,
                fees= 0.0
            )
        
        aapl_trade_liquidated = Trade(
            timestamp=np.uint64(17777000000000),
            trade_id=2,
            leg_id=2,
            ticker=aapl_contract.symbol,
            quantity=round(aapl_position.quantity * -1,4),
            avg_price=current_price,
            trade_value=round(current_price * aapl_position.quantity, 2),
            trade_cost=round(current_price * abs(aapl_position.quantity), 2),
            action=Action.SELL.value,
            fees=0.0
        )

        # Validate
        self.assertEqual(self.dummy_broker.last_trades[aapl_contract], aapl_trade_liquidated)
        self.assertEqual(self.dummy_broker.last_trades[hogs_contract], hogs_trade_liquidated)
   
    def test_return_positions_quantity_not_zero(self):
        # Variables
        ticker = 'HEJ4'
        symbol = self.symbols_map[ticker]

        position = EquityPosition(
                action='SELL',
                quantity= -10,
                avg_price=100,
                quantity_multiplier= symbol.quantity_multiplier,  
                price_multiplier= symbol.price_multiplier,  
                market_price=10

        )
        self.dummy_broker.positions[symbol.contract] = position

        # Test
        result = self.dummy_broker.return_positions()

        # Valdiate
        self.assertEqual(self.dummy_broker.positions[symbol.contract], position)
        self.assertEqual(result, {symbol.contract: position})

    def test_return_positions_quantity_zero(self):
        # Variables
        ticker = 'HEJ4'
        symbol = self.symbols_map[ticker]

        position = EquityPosition(
                action='SELL',
                quantity= 0,
                avg_price=100,
                quantity_multiplier= symbol.quantity_multiplier,  
                price_multiplier= symbol.price_multiplier,  
                market_price=10

        )

        self.dummy_broker.positions[symbol.contract] = position

        # Test
        result =self.dummy_broker.return_positions()

        # Valdiate
        self.assertEqual(result, {symbol.contract: position})
        self.assertEqual(self.dummy_broker.positions, {})
    
    
if __name__ =="__main__":
    unittest.main()
