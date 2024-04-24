import unittest
import numpy as np
from ibapi.order import Order
from contextlib import ExitStack
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from engine.gateways.backtest import BrokerClient
from engine.events import OrderEvent, ExecutionEvent
from engine.gateways.backtest.dummy_broker import PositionDetails, ExecutionDetails

from shared.orders import Action, MarketOrder
from shared.portfolio import AccountDetails, EquityDetails

# TODO: # Type/edge/integration

class TestBrokerClient(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_event_queue = Mock()
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        self.mock_performance_manager = Mock() 
        self.mock_dummy_broker =Mock()

        self.broker_client = BrokerClient(self.mock_event_queue, self.mock_logger,self.mock_portfolio_server,self.mock_performance_manager, self.mock_dummy_broker)
    
    # Basic Validation
    def test_handle_order(self):
        timestamp = 1651500000
        action = Action.LONG
        trade_id = 2
        leg_id =  6
        order = Order()
        contract = Contract()
        
        # Test
        with patch.object(self.mock_dummy_broker, 'placeOrder') as mock_method:
            self.broker_client.handle_order(timestamp, trade_id, leg_id, action, contract, order)
            mock_method.assert_called_once() # check placeOrder called on a valid order event

    def test_on_order(self):
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(self.valid_action, 10)
        self.valid_contract = Contract()

        event = OrderEvent(timestamp=self.valid_timestamp,
                           trade_id=self.valid_trade_id,
                           leg_id=self.valid_leg_id,
                           action=self.valid_action,
                           order=self.valid_order,
                           contract=self.valid_contract)
        
        # Test Valid Order handle_order shoudl be called
        with patch.object(self.broker_client, 'handle_order') as mock_method:
            self.broker_client.on_order(event)
            mock_method.assert_called_once() 
        
    def test_update_positions_valid(self):
        ticker = 'HEJ4'
        contract = Contract()
        contract.symbol = ticker
        multiplier = 1
        price_multiplier=0.01
        quantity_multiplier=4000
        action = Action.SHORT
        quantity = -100
        price = 90
        
        valid_position = PositionDetails(
                action='SELL',
                quantity= quantity,
                avg_cost=round((price * price_multiplier) * (quantity * quantity_multiplier), 2),
                quantity_multiplier= quantity_multiplier,   
                price_multiplier= price_multiplier,      
                initial_margin = 1000,
                unrealizedPnL=0
        )
        self.mock_dummy_broker.return_positions.return_value = {contract :valid_position} # mock position

        # Test portfolio server update postions shoudl be called on postion updates
        with patch.object(self.mock_portfolio_server, 'update_positions') as mock_method:
            self.broker_client.update_positions() # test 
            mock_method.assert_called_once()  # check called

    def test_update_trades_valid(self):
        aapl_contract = Contract()
        aapl_contract.symbol = 'AAPL'
        aapl_contract.secType = 'STK'
        aapl_action = Action.LONG
        aapl_quantity = 10
        aapl_entry_price = 50
        aapl_multiplier = 1
        valid_trade_appl = ExecutionDetails(
                timestamp= np.uint64(165000000),
                trade_id= 1,
                leg_id=1,
                symbol= aapl_contract.symbol,
                quantity= round(aapl_quantity,4),
                price= aapl_entry_price,
                cost= round(aapl_entry_price * aapl_quantity, 2),
                action= aapl_action.value,
                fees= 70 # because not actually a trade
            )
        
        self.mock_dummy_broker.return_executed_trades.return_value = {aapl_contract : valid_trade_appl} # mock trade

        # Test performance manager update trades called on new trade
        with patch.object(self.mock_performance_manager, 'update_trades') as update_trades:
            self.broker_client.update_trades() # test
            update_trades.assert_called_once() # check call

    def test_update_account_valid(self):
        account = AccountDetails(Timestamp=165000000, 
                        FullAvailableFunds = 1000,
                        NetLiquidation= 100000, 
                        FullInitMarginReq= 0, 
                        UnrealizedPnL= 0)
        

        self.mock_dummy_broker.return_account.return_value = account # mock account
        # Test portfolio server account updated on account changes
        with patch.object(self.mock_portfolio_server, 'update_account_details') as mock_update_account_details:
            self.broker_client.update_account() # test
            mock_update_account_details.assert_called_once_with(account) # check update
        
    def test_update_equity_value_valid(self):
        equity = EquityDetails(
                    timestamp= 123456,
                    equity_value =100000
                    )
        # Test 
        with ExitStack() as stack:
            mock_m1 = stack.enter_context(patch.object(self.mock_dummy_broker,'_update_account_equity_value')) # broker shoudl update equity
            mock_m2 = stack.enter_context(patch.object(self.mock_dummy_broker,'return_equity_value', return_value = equity)) # return equity from broker to broker client 
            mock_m3 = stack.enter_context(patch.object(self.mock_performance_manager,'update_equity')) # call performance manager to update equity log
            
            self.broker_client.update_equity_value()
            mock_m1.assert_called_once() 
            mock_m2.assert_called_once()
            mock_m3.assert_called_once_with(equity)

    def test_on_execution(self):
        timestamp = np.uint64(641651500000)
        trade_id = 1 
        leg_id = 2 
        contract = Contract()
        contract.symbol = 'AAPL'
        quantity = -10
        action =  Action.LONG
        fill_price = 9.9 
        fees = 90.9
        valid_trade = ExecutionDetails(
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            symbol = contract.symbol,
            quantity = round(quantity,4),
            price = fill_price,
            cost = round(fill_price * quantity, 2),
            action = action.value,
            fees = round(fees,4)
        )
        self.valid_contract = Contract()
        self.valid_order = Order()
    
        exec = ExecutionEvent(timestamp=timestamp,
                               trade_details=valid_trade,
                               action=action,
                               contract=contract)
        
        with ExitStack() as stack:
            mock_m1 = stack.enter_context(patch.object(self.broker_client,'update_positions'))
            mock_m2 = stack.enter_context(patch.object(self.broker_client,'update_account'))
            mock_m3 = stack.enter_context(patch.object(self.broker_client,'update_equity_value'))
            mock_m4 = stack.enter_context(patch.object(self.broker_client,'update_trades'))

            self.broker_client.on_execution(exec)

            mock_m1.assert_called_once()
            mock_m2.assert_called_once()
            mock_m3.assert_called_once()
            mock_m4.assert_called_once()

    # Type/edge/integration
            
if __name__ =="__main__":
    unittest.main()