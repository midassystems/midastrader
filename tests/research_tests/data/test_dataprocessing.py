import unittest
import pandas as pd
from datetime import datetime
from typing import List, Dict
from unittest.mock import Mock
from pandas.testing import assert_frame_equal

from midas.research.data import DataProcessing

def valid_process_data(db_response: List[Dict]):
    df = pd.DataFrame(db_response)
    df.drop(columns=['id'], inplace=True)

    # Convert OHLCV columns to floats
    ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
    df[ohlcv_columns] = df[ohlcv_columns].astype(float)

    df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

    return df

class TestDataProcessing(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_db = Mock()
        self.data_processor = DataProcessing(self.mock_db)
        self.valid_tickers = ['HE.n.0', 'ZC.n.0']
        self.valid_start_date = '2022-05-01'
        self.valid_end_date = '2022-05-03'

        self.valid_db_response = [{"id":49252,"timestamp":"1651500000000000000","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"1651500000000000000","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49257,"timestamp":"1651503600000000000","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49256,"timestamp":"1651503600000000000","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                  {"id":49258,"timestamp":"1651507200000000000","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"1651507200000000000","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49263,"timestamp":"1651510800000000000","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
                                  {"id":49262,"timestamp":"1651510800000000000","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
        ]
        
        # Create Properly processed response
        self.valid_processed_data = valid_process_data(self.valid_db_response)
    
    # Basic Validation
    def test_process_bardata_valid(self):
        df = pd.DataFrame(self.valid_db_response)
        df.drop(columns=['id'], inplace=True)

        # Test
        result = self.data_processor._process_bardata(df)
        
        # Validation
        assert_frame_equal(result, self.valid_processed_data, check_dtype=True)
    
    def test_get_data_valid(self):
        self.mock_db.get_bar_data.return_value = self.valid_db_response  # mock database response

        # Test
        result = self.data_processor.get_data(tickers=self.valid_tickers, 
                                  start_date=self.valid_start_date, 
                                  end_date=self.valid_end_date)

        # Validate call was made to database client
        self.mock_db.get_bar_data.assert_called_once_with(tickers=self.valid_tickers, 
                                                                 start_date=self.valid_start_date, 
                                                                 end_date=self.valid_end_date)
        # Validate Dataframe 
        assert_frame_equal(result, self.valid_processed_data, check_dtype=True)
    
    # Type Check
    def test_get_data_tickers_type_validation(self):
        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_processor.get_data(tickers='AAPL', 
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)

    def test_get_data_tickers_item_type_validation(self):
        with self.assertRaisesRegex(TypeError, "All items in 'tickers' must be of type string."):
            self.data_processor.get_data(tickers=[1,2,3], 
                start_date=self.valid_start_date, 
                end_date=self.valid_end_date)

    def test_get_data_invalid_missing_values_strategy(self):
        with self.assertRaisesRegex(ValueError, "'missing_value_strategy' must either 'fill_forward' or 'drop' of type str."):
            self.data_processor.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date,
                            missing_values_strategy='testing')
            
    def test_get_data_invalid_date_type(self):
        self.invalid_end_date = datetime(2021,1,1)
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_processor.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=self.invalid_end_date)
            
    def test_get_data_invalid_date_fromat(self):
        self.invalid_start_date = "01-01-2024"
        with self.assertRaisesRegex(ValueError,"Invalid timestamp format. Required format: YYYY-MM-DDTHH:MM:SS"):
            self.data_processor.get_data(tickers=self.valid_tickers,
                            start_date=self.invalid_start_date, 
                            end_date=self.valid_end_date)

    def test_missing_tickers(self):
        with self.assertRaisesRegex(TypeError,"'tickers' must be a list of strings."):
            self.data_processor.get_data(tickers=None,
                            start_date=self.valid_start_date, 
                            end_date=self.valid_end_date)
            
    def test_missing_start_date(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_processor.get_data(tickers=self.valid_tickers,
                            start_date=None, 
                            end_date=self.valid_end_date)
            
    def test_missing_end_date(self):
        with self.assertRaisesRegex(TypeError,"'timestamp' must be of type str."):
            self.data_processor.get_data(tickers=self.valid_tickers,
                            start_date=self.valid_start_date, 
                            end_date=None)

if __name__ =="__main__":
    unittest.main()
