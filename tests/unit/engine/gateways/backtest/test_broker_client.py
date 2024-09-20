import unittest
import numpy as np
from ibapi.order import Order
from contextlib import ExitStack
from ibapi.contract import Contract
from midas.shared.trade import Trade
from unittest.mock import Mock, patch
from midas.shared.positions import EquityPosition
from midas.shared.orders import Action, MarketOrder
from midas.shared.account import Account, EquityDetails
from midas.engine.gateways.backtest import BrokerClient
from midas.engine.events import OrderEvent, ExecutionEvent


class TestBrokerClient(unittest.TestCase):
    def setUp(self) -> None:
        # Mock objects
        self.mock_event_queue = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        self.mock_performance_manager = Mock() 
        self.mock_dummy_broker =Mock()
        self.eod_event_flag = Mock()

        # BrokerClient instance
        self.broker_client = BrokerClient(
                                          self.mock_event_queue, 
                                          self.mock_logger,
                                          self.mock_portfolio_server,
                                          self.mock_performance_manager, 
                                          self.mock_dummy_broker, 
                                          self.eod_event_flag
                                        )
    
    # Basic Validation
    def test_handle_order(self):
        # Mock order
        timestamp = 1651500000
        action = Action.LONG
        trade_id = 2
        leg_id =  6
        order = Order()
        contract = Contract()
        
        with patch.object(self.mock_dummy_broker, 'placeOrder') as mock_method:
            # Test
            self.broker_client.handle_order(timestamp, trade_id, leg_id, action, contract, order)

            # Validate
            mock_method.assert_called_once()

    def test_on_order(self):
        # Order data
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(self.valid_action, 10)
        self.valid_contract = Contract()

        # Order event
        event = OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
        
        with patch.object(self.broker_client, 'handle_order') as mock_method:
            # Test
            self.broker_client.on_order(event)

            # Validate
            mock_method.assert_called_once() 
        
    def test_update_positions_valid(self):
        # Position data
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        multiplier = 1
        price_multiplier=0.01
        quantity_multiplier=4000
        action = Action.SHORT
        quantity = -100
        price = 90
        
        # Position object
        valid_position = EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 100,
            quantity_multiplier = 1,
            price_multiplier = 1,
            market_price=12 
        )
        self.mock_dummy_broker.return_positions.return_value = {contract :valid_position} 

        with patch.object(self.mock_portfolio_server, 'update_positions') as mock_method:
            # Test
            self.broker_client.update_positions()

            # Validate
            mock_method.assert_called_once()

    def test_update_trades_valid(self):
        # Trade data
        aapl_contract = Contract()
        aapl_contract.symbol = 'AAPL'
        aapl_contract.secType = 'STK'
        aapl_action = Action.LONG
        aapl_quantity = 10
        aapl_entry_price = 50
        aapl_multiplier = 1

        # Execution details
        valid_trade_appl = Trade(
            timestamp= np.uint64(165000000),
            trade_id= 1,
            leg_id=1,
            ticker= aapl_contract.symbol,
            quantity= round(aapl_quantity,4),
            avg_price= aapl_entry_price,
            trade_value=round(aapl_entry_price * aapl_quantity, 2),
            trade_cost=round(aapl_entry_price * aapl_quantity, 2),
            action= aapl_action.value,
            fees= 70 
        )
        
        # Mock response
        self.mock_dummy_broker.return_executed_trades.return_value = {aapl_contract : valid_trade_appl} 

        with patch.object(self.mock_performance_manager, 'update_trades') as update_trades:
            # Test
            self.broker_client.update_trades() 

            # Validate
            update_trades.assert_called_once()

    def test_update_account_valid(self):
        # Account object
        account = Account(
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
        
        # Mock dummy broker response
        self.mock_dummy_broker.return_account.return_value = account 

        with patch.object(self.mock_portfolio_server, 'update_account_details') as mock_update_account_details:
            # Test
            self.broker_client.update_account() 

            # Validate
            mock_update_account_details.assert_called_once_with(account) 
        
    def test_update_equity_value_valid(self):
        # Equity details dict
        equity = EquityDetails(timestamp= 123456, equity_value =100000)

        with ExitStack() as stack:
            mock_m1 = stack.enter_context(patch.object(self.mock_dummy_broker,'_update_account')) # broker shoudl update equity
            mock_m2 = stack.enter_context(patch.object(self.mock_dummy_broker,'return_equity_value', return_value = equity)) # return equity from broker to broker client 
            mock_m3 = stack.enter_context(patch.object(self.mock_performance_manager,'update_equity')) # call performance manager to update equity log
            
            # Test
            self.broker_client.update_equity_value()
            
            # Validate
            mock_m1.assert_called_once() 
            mock_m2.assert_called_once()
            mock_m3.assert_called_once_with(equity)

    def test_on_execution(self):
        # Trade details
        timestamp = np.uint64(641651500000)
        trade_id = 1 
        leg_id = 2 
        contract = Contract()
        contract.symbol = 'AAPL'
        quantity = -10
        action =  Action.LONG
        fill_price = 9.9 
        fees = 90.9

        # Execution dict
        valid_trade = Trade(            
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            ticker = contract.symbol,
            quantity = round(quantity,4),
            avg_price = fill_price,
            trade_value=round(fill_price * quantity, 2),
            trade_cost = round(fill_price * quantity, 2),
            action = action.value,
            fees = round(fees,4)
        )
        self.valid_contract = Contract()
        self.valid_order = Order()

        # Executiom event
        exec = ExecutionEvent(timestamp=timestamp,
                               trade_details=valid_trade,
                               action=action,
                               contract=contract)
        
        with ExitStack() as stack:
            mock_m1 = stack.enter_context(patch.object(self.broker_client,'update_positions'))
            mock_m2 = stack.enter_context(patch.object(self.broker_client,'update_account'))
            mock_m3 = stack.enter_context(patch.object(self.broker_client,'update_equity_value'))
            mock_m4 = stack.enter_context(patch.object(self.broker_client,'update_trades'))

            # Mock last trade
            self.broker_client.broker.last_trade = valid_trade

            # Test
            self.broker_client.on_execution(exec)

            # Validate
            mock_m1.assert_called_once()
            mock_m2.assert_called_once()
            mock_m3.assert_called_once()
            mock_m4.assert_called_once()
            
if __name__ =="__main__":
    unittest.main()
