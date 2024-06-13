import unittest
import numpy as np
import pandas as pd
from queue import Queue
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock
from midas.engine.events import MarketEvent
from midas.shared.market_data import BarData
from midas.engine.gateways.backtest import DataClient

def process_db_response(db_response: list):
    """ Create Properly processed response. """ 
    df = pd.DataFrame(db_response)
    df.drop(columns=['id'], inplace=True)
    df['timestamp'] = df['timestamp'].astype(np.uint64)
    df['open'] = df['open'].apply(Decimal)
    df['high'] = df['high'].apply(Decimal)
    df['low'] = df['low'].apply(Decimal)
    df['close'] = df['close'].apply(Decimal)
    df['volume'] = df['volume'].astype(np.uint64)
    processed_df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
    return processed_df 


class TestDataClient(unittest.TestCase):
    def setUp(self) -> None:
        # Mock objects
        self.event_queue = Mock()
        self.mock_db_client = Mock()
        self.mock_order_book = Mock()
        self.eod_event_flag = Mock()

        # Dataclient instance
        self.data_client = DataClient(event_queue=self.event_queue, data_client=self.mock_db_client, order_book=self.mock_order_book, eod_event_flag=self.eod_event_flag)

        # Mock data retrieval parameters
        self.valid_tickers = ['HE.n.0', 'ZC.n.0']
        self.valid_start_date = '2022-05-01'
        self.valid_end_date = '2022-05-02'

        # Mock database response
        self.valid_db_response = [{"id":49252,"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"1651518000000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                  {"id":49257,"timestamp":"1651518000000000000","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]
        
        # Properly processed db response
        self.valid_processed_data = process_db_response(self.valid_db_response)

        # Extracted timestamps
        self.valid_unique_timestamps  = self.valid_processed_data['timestamp'].unique().tolist()
    
    # Basic Validation
    def test_process_bardata_valid(self):
        df = pd.DataFrame(self.valid_db_response)
        df.drop(columns=['id'], inplace=True)

        # Test
        result = self.data_client._process_bardata(df)
        
        # Validate
        pd.testing.assert_frame_equal(result, self.valid_processed_data, check_dtype=True)
    
    def test_get_data_valid(self):
        # Mock database response
        self.mock_db_client.get_bar_data.return_value = self.valid_db_response 

        # Test
        self.data_client.get_data(tickers=self.valid_tickers, 
                                  start_date=self.valid_start_date, 
                                  end_date=self.valid_end_date)

        # Validate call was made to database client
        self.mock_db_client.get_bar_data.assert_called_once_with(tickers=self.valid_tickers, 
                                                                 start_date=self.valid_start_date, 
                                                                 end_date=self.valid_end_date)
        
        # Validate Dataframe
        # Ensure both DataFrames are sorted by 'timestamp' and 'symbol'
        self.valid_processed_data = self.valid_processed_data.sort_values(by=['timestamp', 'symbol']).reset_index(drop=True)
        result = self.data_client.data.sort_values(by=['timestamp', 'symbol']).reset_index(drop=True)
        pd.testing.assert_frame_equal(result, self.valid_processed_data, check_dtype=True)

        # Validate Unique Timestamsp
        unique_timestamps  = self.unique_dates = self.valid_processed_data['timestamp'].unique().tolist()
        self.assertEqual(self.data_client.unique_timestamps,unique_timestamps)
    
    def test_get_latest_data(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps
        self.data_client.next_date = self.valid_unique_timestamps[0]

        # Test 
        results = self.data_client._get_latest_data()

        # Expected
        valid_result = self.valid_processed_data[self.valid_processed_data['timestamp'] == self.valid_unique_timestamps[0]]
        
        # Validate
        pd.testing.assert_frame_equal(results,  valid_result, check_dtype=True) 
        self.assertEqual(type(results), pd.DataFrame) 
        # All the timestamps should be equal 
        for index, row in valid_result.iterrows():
            self.assertEqual(row['timestamp'], self.data_client.next_date)

    def test_set_market_data(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps
        self.data_client.next_date = self.valid_unique_timestamps[0]

        # Test 
        self.data_client._set_market_data()

        # Validate
        self.assertTrue(self.mock_order_book.update_market_data.called) 
        called_with_arg = self.mock_order_book.update_market_data.call_args[1]
        self.assertEqual(called_with_arg['timestamp'],self.data_client.next_date)

        # Validate the contents of call
        for ticker, bar_data in called_with_arg['data'].items():
            self.assertIn(ticker, self.valid_tickers, f"Unexpected ticker {ticker} found in MarketDataEvent.")
        

    def test_data_stream(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps

        # Test
        while self.data_client.data_stream():
            # Validate
            self.assertTrue(self.mock_order_book.update_market_data.called) 
            called_with_arg = self.mock_order_book.update_market_data.call_args[1]
            self.assertEqual(called_with_arg['timestamp'],self.data_client.next_date)

            # Validate the contents of call
            for ticker, bar_data in called_with_arg['data'].items():
                self.assertIn(ticker, self.valid_tickers, f"Unexpected ticker {ticker} found in MarketDataEvent.")
            
        # Stream should go right up to the last date            
        self.assertEqual(self.data_client.next_date, self.valid_unique_timestamps[-1]) 

    # Type Check
    def test_type_check(self):
        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_client.get_data(tickers='AAPL', 
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)

        with self.assertRaisesRegex(TypeError, "All items in 'tickers' must be of type string."):
            self.data_client.get_data(tickers=[1,2,3], 
                start_date=self.valid_start_date, 
                end_date=self.valid_end_date)

        with self.assertRaisesRegex(ValueError, "'missing_value_strategy' must either 'fill_forward' or 'drop' of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date,
                            missing_values_strategy='testing')
            
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=datetime(2021,1,1))
            
        with self.assertRaisesRegex(ValueError,"Invalid timestamp format. Required format: YYYY-MM-DDTHH:MM:SS"):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date="01-01-2024", 
                            end_date=self.valid_end_date)

        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_client.get_data(tickers=None,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)
            
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=None, 
                            end_date=self.valid_end_date)
            
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=None)
            

if __name__ == "__main__":
    unittest.main()