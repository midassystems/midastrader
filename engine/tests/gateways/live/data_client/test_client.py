import unittest
from decouple import config
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import Mock, patch

from engine.gateways.live import DataClient
from engine.events import OrderEvent, ExecutionEvent, Action, MarketDataType

#TODO: edge cases

class TestDataClient(unittest.TestCase):
    def setUp(self):
        # Mock the logger and the queue to pass into DataClient
        self.mock_logger = Mock()
        self.mock_event_queue = Mock()
        self.mock_order_book = Mock()

        self.data_client = DataClient(event_queue=self.mock_event_queue, 
                                        order_book=self.mock_order_book,
                                            logger=self.mock_logger,
                                            host='127.0.0.0',
                                            port= "7497",
                                            clientId=1,
                                            ib_account= "U1234567")
        self.data_client.app = Mock()
        self.data_client.app.reqId_to_symbol_map = {}


    # Basic Validation
    def test_get_valid_id(self):
        id = 10
        # test 
        self.data_client.app.next_valid_order_id = id # mock next valid id
        current_id = self.data_client._get_valid_id()
        # validate
        self.assertEqual(current_id, id)
        self.assertEqual(self.data_client.app.next_valid_order_id, id+1)

    def test_is_connected(self):
        # isConnected checks app's connection status
        self.data_client.app.isConnected.return_value = True
        self.assertTrue(self.data_client.is_connected())
        self.data_client.app.isConnected.assert_called_once()

    def test_connect(self):
        # Ensure connect method starts a thread and waits for connection events
        with patch('threading.Thread.start', return_value=None) as mock_thread_start:
            self.data_client.connect()
            mock_thread_start.assert_called_once()
            self.mock_logger.info.assert_called_with('Waiting For Data Connection...')
            self.data_client.app.connected_event.wait.assert_called_once()
            self.data_client.app.valid_id_event.wait.assert_called_once()

    def test_disconnect(self):
        # Disconnect simply calls app.disconnect
        self.data_client.disconnect()
        self.data_client.app.disconnect.assert_called_once()

    def test_get_data_bar(self):
        contract = Contract()
        data_type = MarketDataType.BAR

        with patch.object(self.data_client, 'stream_5_sec_bars') as mock_method:
            self.data_client.get_data(data_type, contract)
            mock_method.assert_called_once_with(contract)

    def test_get_data_quote(self):
        contract = Contract()
        data_type = MarketDataType.QUOTE

        with patch.object(self.data_client, 'stream_quote_data') as mock_method:
            self.data_client.get_data(data_type, contract)
            mock_method.assert_called_once_with(contract)
    
    def test_stream_5_sec_bars(self):
        contract = Contract()
        contract.symbol = 'AAPL'

        with patch.object(self.data_client, '_get_valid_id', return_value= 123) as mock_method:
            self.data_client.stream_5_sec_bars(contract=contract)
            self.data_client.app.reqRealTimeBars.assert_called_once_with(reqId=123, contract=contract, barSize=5, whatToShow='TRADES', useRTH=False, realTimeBarsOptions=[])
            self.assertEqual(self.data_client.app.reqId_to_symbol_map[123], "AAPL")
            self.mock_logger.info.assert_called_once()

    def test_stream_5_sec_bars_already_streaming(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        self.data_client.app.reqId_to_symbol_map = {321: contract.symbol}
        with patch.object(self.data_client, '_get_valid_id', return_value= 123) as mock_method:
            self.data_client.stream_5_sec_bars(contract=contract)
            self.mock_logger.error.assert_called_once_with(f"Data stream already established for {contract}.")
            self.assertFalse(self.data_client.app.reqRealTimeBars.called)

    def test_stream_quote_data(self):
        contract = Contract()
        contract.symbol = 'AAPL'

        with patch.object(self.data_client, '_get_valid_id', return_value= 123) as mock_method:
            self.data_client.stream_quote_data(contract=contract)
            self.data_client.app.reqMktData.assert_called_once_with(reqId=123, contract=contract,genericTickList="", snapshot=False, regulatorySnapshot=False, mktDataOptions=[])
            self.assertEqual(self.data_client.app.reqId_to_symbol_map[123], "AAPL")
            self.mock_logger.info.assert_called_once()

    def test_stream_quote_data_already_streaming(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        self.data_client.app.reqId_to_symbol_map = {321: contract.symbol}

        with patch.object(self.data_client, '_get_valid_id', return_value= 123) as mock_method:
            self.data_client.stream_quote_data(contract=contract)
            self.mock_logger.error.assert_called_once_with(f"Data stream already established for {contract}.")
            self.assertFalse(self.data_client.app.reqRealTimeBars.called)

    def test_cancel_all_bar_data(self):
        contract = Contract()
        contract.symbol = 'AAPL'

        self.data_client.app.reqId_to_symbol_map = {321: contract.symbol}

        self.data_client.cancel_all_bar_data()
        self.assertEqual(self.data_client.app.reqId_to_symbol_map, {})

    def test_cancel_all_quote_data(self):
        contract = Contract()
        contract.symbol = 'AAPL'

        self.data_client.app.reqId_to_symbol_map = {321: contract.symbol}

        self.data_client.cancel_all_quote_data()
        self.assertEqual(self.data_client.app.reqId_to_symbol_map, {})

    # Type Validation
    def test_get_data_valueerror(self):
        contract = Contract()
        data_type = 'BAR'

        with self.assertRaisesRegex(ValueError,"'data_type' must be of type MarketDataType enum."):
            self.data_client.get_data(data_type, contract)
        

if __name__ == '__main__':
    unittest.main()