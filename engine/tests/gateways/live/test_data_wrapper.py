import unittest
import numpy as np
from decimal import Decimal
from unittest.mock import Mock, patch

from engine.events import MarketEvent
from engine.gateways.live.data_client.wrapper import DataApp

from shared.market_data import BarData

# TODO: edge cases
class TestDataApp(unittest.TestCase):
    def setUp(self):
        self.mock_event_queue = Mock()
        self.mock_logger = Mock()
        self.mock_order_book = Mock()
        self.data_app = DataApp(event_queue=self.mock_event_queue,order_book=self.mock_order_book, logger=self.mock_logger)

    def test_200_error_valid(self):
        # Simulate an error code for contract not found
        # test
        self.data_app.error(reqId=-1, errorCode=200, errorString="Contract not found")
        
        # validate
        self.mock_logger.critical.assert_called_once_with("200 : Contract not found") # Verify critical log is called with expected message
        self.assertFalse(self.data_app.is_valid_contract) # Verify is_valid_contract is set to False
        self.assertTrue(self.data_app.validate_contract_event.is_set()) # Verify validate_contract_event is set

    def test_connectAck_valid(self):
        # test
        self.data_app.connectAck()
        
        # validate
        self.mock_logger.info.assert_called_once_with('Established Data Connection') # Verify critical log is called with expected message
        self.assertFalse(self.data_app.is_valid_contract) # Verify is_valid_contract is set to False
        self.assertTrue(self.data_app.connected_event.is_set()) # Verify validate_contract_event is set

    def test_connection_closed(self):
        # test
        self.data_app.connectionClosed()
        
        # validate
        self.mock_logger.info.assert_called_once_with('Closed Data Connection.')

    def test_nextvalidId_valid(self):
        id = 10
        # test
        self.data_app.nextValidId(id)
        
        # validate
        self.assertEqual(self.data_app.next_valid_order_id, id)
        self.mock_logger.info.assert_called_once_with(f"Next Valid Id {id}")
        self.assertTrue(self.data_app.valid_id_event.is_set()) 

    def test_contractDetails(self):
        # test
        self.data_app.contractDetails(10, None)
        
        # validate
        self.assertTrue(self.data_app.is_valid_contract)

    def test_contractDetailsEnd_valid(self):
        # test
        self.data_app.contractDetailsEnd(10)

        # validate
        self.assertTrue(self.data_app.validate_contract_event.is_set())

    def test_realtimeBar(self):
        self.data_app.reqId_to_symbol_map[123] = 'AAPL'

        reqId = 123
        time = np.uint64(165500000)
        open = Decimal(109.9)
        high = Decimal(110)
        low = Decimal(105.6)
        close = Decimal(108)
        volume = Decimal(10000)
        wap = 109 
        count = 10
        valid_bar = BarData(
                            ticker='AAPL',
                            timestamp=np.uint64(time * 1e9),
                            open=open, 
                            high=high,
                            low=low,
                            close=close,
                            volume=np.uint64(volume))
        # test
        self.data_app.realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        
        # validate
        self.mock_order_book.update_market_data.assert_called_once_with(timestamp=np.uint64(time * 1e9), data={'AAPL':valid_bar})
        self.assertEqual(self.data_app.current_bar_data, {})

if __name__ == '__main__':
    unittest.main()
