import unittest
import numpy as np
import pandas as pd
from queue import Queue
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock
from pandas.testing import assert_frame_equal

from midas.engine.events import MarketEvent
from midas.shared.market_data import BarData
from midas.engine.gateways.backtest import DataClient

#TODO: edge cases

class TestDataClient(unittest.TestCase):
    def setUp(self) -> None:
        self.event_queue = Mock()
        self.mock_db_client = Mock()
        self.mock_order_book = Mock()
        self.data_client = DataClient(event_queue=self.event_queue, data_client=self.mock_db_client, order_book=self.mock_order_book)

        self.valid_tickers = ['HE.n.0', 'ZC.n.0']
        self.valid_start_date = '2022-05-01'
        self.valid_end_date = '2022-05-02'

        self.valid_db_response = [{"id":49252,"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"1651518000000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                  {"id":49257,"timestamp":"1651518000000000000","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]
        
        # Create Properly processed response
        df = pd.DataFrame(self.valid_db_response)
        df.drop(columns=['id'], inplace=True)
        df['timestamp'] = df['timestamp'].astype(np.uint64)
        df['open'] = df['open'].apply(Decimal)
        df['high'] = df['high'].apply(Decimal)
        df['low'] = df['low'].apply(Decimal)
        df['close'] = df['close'].apply(Decimal)
        df['volume'] = df['volume'].astype(np.uint64)
        self.valid_processed_data = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

        # Extracting timestamps without converting them to dates to keep the unique timestamp values
        self.valid_unique_timestamps  = self.valid_processed_data['timestamp'].unique().tolist()
    
    # Basic Validation
    def test_handle_fill_forward_null_values(self):
        response_missing_data = [{"id":49252,"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"1651518000000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                #   {"id":49257,"timestamp":"1651518000000000000","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]

        fill_forward_df = pd.DataFrame([{"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                        {"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                        {"timestamp":"1651518000000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                        {"timestamp":"1651518000000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                        {"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                        {"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                        {"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                        {"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ])
        
        # Expected df
        fill_forward_df['volume'] = fill_forward_df['volume'].astype('float64')
        fill_forward_df = fill_forward_df.sort_values(by=['timestamp', 'symbol']).reset_index(drop=True)

        # Test 
        df = pd.DataFrame(response_missing_data)
        df.drop(columns=['id'], inplace=True)
        result = self.data_client._handle_null_values(data=df, missing_values_strategy='fill_forward')

        # Validation
        assert_frame_equal(result, fill_forward_df, check_dtype=True)

    def test_handle_drop_null_values(self):
        response_missing_data = [{"id":49252,"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"1651518000000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                #   {"id":49257,"timestamp":"1651518000000000000","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]

        drop_df = pd.DataFrame([{"timestamp":"1651514400000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                        {"timestamp":"1651514400000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                        {"timestamp":"1651521600000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                        {"timestamp":"1651521600000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                        {"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                        {"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ])
        
        # Convert strings to datetime for proper comparison
        drop_df['volume'] = drop_df['volume'].astype('float64')
        drop_df = drop_df.sort_values(by=['timestamp', 'symbol']).reset_index(drop=True)

        # Test 
        df = pd.DataFrame(response_missing_data)
        df.drop(columns=['id'], inplace=True)
        result = self.data_client._handle_null_values(data=df, missing_values_strategy='drop')

        # Validation
        assert_frame_equal(result, drop_df, check_dtype=True)
    
    def test_process_bardata_valid(self):
        df = pd.DataFrame(self.valid_db_response)
        df.drop(columns=['id'], inplace=True)

        # Test
        result = self.data_client._process_bardata(df)
        
        # Validation
        assert_frame_equal(result, self.valid_processed_data, check_dtype=True)
    
    def test_get_data_valid(self):
        self.mock_db_client.get_bar_data.return_value = self.valid_db_response  # mock database response

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
        assert_frame_equal(result, self.valid_processed_data, check_dtype=True)

        # Validate Unique Timestamsp
        unique_timestamps  = self.unique_dates = self.valid_processed_data['timestamp'].unique().tolist()
        self.assertEqual(self.data_client.unique_timestamps,unique_timestamps)
    
    def test_get_latest_data(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps
        self.data_client.next_date = self.valid_unique_timestamps[0]

        # Expected
        valid_result = self.valid_processed_data[self.valid_processed_data['timestamp'] == self.valid_unique_timestamps[0]]

        # Test 
        results = self.data_client._get_latest_data()
        
        # Validation
        assert_frame_equal(results,  valid_result, check_dtype=True) # exepected results
        self.assertEqual(type(results), pd.DataFrame) # check the data type
        for index, row in valid_result.iterrows():
            self.assertEqual(row['timestamp'], self.data_client.next_date) # verify all the timestamps equal expected

    def test_set_market_data(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps
        self.data_client.next_date = self.valid_unique_timestamps[0]

        # Test 
        self.data_client._set_market_data()

        # Validation
        self.assertTrue(self.mock_order_book.update_market_data.called) 
        called_with_arg = self.mock_order_book.update_market_data.call_args[1]

        # validate the contents of call
        for ticker, bar_data in called_with_arg['data'].items():
            self.assertIn(ticker, self.valid_tickers, f"Unexpected ticker {ticker} found in MarketDataEvent.")
        
        self.assertEqual(called_with_arg['timestamp'],self.data_client.next_date)

    def test_data_stream(self):
        self.data_client.data = self.valid_processed_data
        self.data_client.unique_timestamps = self.valid_unique_timestamps

        #test
        while self.data_client.data_stream():
            # validate
            self.assertTrue(self.mock_order_book.update_market_data.called) 
            called_with_arg = self.mock_order_book.update_market_data.call_args[1]

            # validate the contents of call
            for ticker, bar_data in called_with_arg['data'].items():
                self.assertIn(ticker, self.valid_tickers, f"Unexpected ticker {ticker} found in MarketDataEvent.")
            
            self.assertEqual(called_with_arg['timestamp'],self.data_client.next_date)
            
        self.assertEqual(self.data_client.next_date, self.valid_unique_timestamps[-1]) # test that stream does right up to the last date

    # Type Check
    def test_get_data_tickers_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_client.get_data(tickers='AAPL', 
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)

    def test_get_data_tickers_item_type_validation(self):
        with self.assertRaisesRegex(TypeError, "All items in 'tickers' must be of type string."):
            self.data_client.get_data(tickers=[1,2,3], 
                start_date=self.valid_start_date, 
                end_date=self.valid_end_date)

    def test_get_data_invalid_missing_values_strategy(self):
        with self.assertRaisesRegex(ValueError, "'missing_value_strategy' must either 'fill_forward' or 'drop' of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date,
                            missing_values_strategy='testing')
            
    def test_get_data_invalid_date_type(self):
        self.invalid_end_date = datetime(2021,1,1)
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=self.invalid_end_date)
            
    def test_get_data_invalid_date_fromat(self):
        self.invalid_start_date = "01-01-2024"
        with self.assertRaisesRegex(ValueError,"Invalid timestamp format. Required format: YYYY-MM-DDTHH:MM:SS"):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.invalid_start_date, 
                            end_date=self.valid_end_date)

    def test_missing_tickers(self):
        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_client.get_data(tickers=None,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)
            
    def test_missing_start_date(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=None, 
                            end_date=self.valid_end_date)
            
    def test_missing_end_date(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_client.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=None)

    # Edge Cases
            
    # No Data for time range, 
            
    # start date after end date
            
    # start date in the future or end date in the future
            

if __name__ == "__main__":
    unittest.main()