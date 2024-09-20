import unittest
import numpy as np
from decouple import config
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import Mock, patch
from midas.shared.account import Account
from midas.engine.events import OrderEvent
from midas.shared.orders import Action, BaseOrder, MarketOrder
from midas.engine.gateways.live.broker_client import BrokerClient

class TestBrokerClient(unittest.TestCase):
    def setUp(self):
        # Mock objects
        self.mock_logger = Mock()
        self.mock_event_queue = Mock()
        self.mock_portfolio_server = Mock()
        self.mock_performance_manager = Mock()

        # BrokerClient instance
        self.broker_client = BrokerClient(event_queue=self.mock_event_queue, 
                                            logger=self.mock_logger,
                                            portfolio_server=self.mock_portfolio_server,
                                            performance_manager=self.mock_performance_manager,
                                            host='127.0.0.0',
                                            port= "7497",
                                            clientId=1,
                                            ib_account= "U1234567")
        # Mock BrokerWrapper
        self.broker_client.app = Mock()

    # Basic Validation
    def test_get_valid_id(self):
        # Set next validId
        id = 10
        self.broker_client.app.next_valid_order_id = id
        
        # Test
        current_id = self.broker_client._get_valid_id()

        # Validate
        self.assertEqual(current_id, id)
        self.assertEqual(self.broker_client.app.next_valid_order_id, id+1)

    def test_is_connected(self):
        # Test
        self.broker_client.app.isConnected.return_value = True

        # Validate
        self.assertTrue(self.broker_client.is_connected())
        self.broker_client.app.isConnected.assert_called_once()

    def test_connect(self):
        # Ensure connect method starts a thread and waits for connection events
        with patch('threading.Thread.start', return_value=None) as mock_thread_start:
            # Test
            self.broker_client.connect()

            # Validate
            mock_thread_start.assert_called_once()
            self.mock_logger.info.assert_called_with('Waiting For Broker Connection...')
            self.broker_client.app.connected_event.wait.assert_called_once()
            self.broker_client.app.valid_id_event.wait.assert_called_once()

    def test_disconnect(self):
        # Test
        self.broker_client.disconnect()
        
        # Validate
        self.broker_client.app.disconnect.assert_called_once()

    def test_on_order_valid(self):
        # Mock order event
        self.valid_timestamp = np.uint64(1651500000)
        self.valid_action = Action.LONG
        self.valid_trade_id = 2
        self.valid_leg_id =  6
        self.valid_order = MarketOrder(action=self.valid_action, quantity=10)
        self.valid_contract = Contract()

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
            mock_method.assert_called_once_with(self.valid_contract, self.valid_order.order) 

    def test_handle_order(self):
        # Mock order
        id = 10
        self.valid_order = Order()
        self.valid_contract = Contract()
        self.broker_client.app.next_valid_order_id = id

        with patch.object(self.broker_client.app, 'placeOrder') as mock_method:
            # Test
            self.broker_client.handle_order(self.valid_contract, self.valid_order)
            
            # Validate
            mock_method.assert_called_once_with(orderId=id, contract=self.valid_contract, order=self.valid_order)
            self.assertEqual(self.broker_client.app.next_valid_order_id, id+1)
    
    def test_request_account_summary(self):
        self.broker_client._get_valid_id = Mock(return_value=10)
        expected_tags_string = "Timestamp,FullAvailableFunds,FullInitMarginReq,NetLiquidation,UnrealizedPnL,FullMaintMarginReq,ExcessLiquidity,Currency,BuyingPower,FuturesPNL,TotalCashBalance"

        with patch.object(self.broker_client.app, 'reqAccountSummary') as mock_method:
            # Test
            self.broker_client.request_account_summary()
            
            # Validate
            mock_method.assert_called_once_with(10, "All",expected_tags_string)

    # Type Validation
    def test_on_order_valueerror(self):
        with self.assertRaisesRegex(ValueError,"'event' must be of type OrderEvent instance."):
            self.broker_client.on_order('event')
            
    
if __name__ == "__main__":
    unittest.main()