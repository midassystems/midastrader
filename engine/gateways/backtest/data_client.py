import pandas as pd
from queue import Queue
from datetime import datetime
from typing import Dict, List

from client import DatabaseClient
from engine.events import MarketEvent, BarData, EODEvent
from engine.order_book import OrderBook

class DataClient(DatabaseClient):
    def __init__(self, event_queue: Queue, data_client: DatabaseClient, order_book:OrderBook):
        """
        Class constructor.

        Args:
            event_queue (Queue) : The main event queue, new MarketDataEvents are added to this queue.
            data_client (DatabaseClient) : Responsible for interacting with the database to pull the data via a client class based on a Django Rest-Framework API.
        
        """
        self.event_queue = event_queue
        self.data_client = data_client
        self.order_book = order_book
        
        # Data 
        self.data : pd.DataFrame
        self.unique_timestamps : list
        self.next_date = None
        self.current_date_index = -1
        self.current_day = None

    def get_data(self, tickers:List[str], start_date: str, end_date: str, missing_values_strategy: str = 'fill_forward'):
        """
        Retrieves data from the database and initates the data processing. Stores initial data response in self.price_log.

        Args:
            symbols (List[str]) : A list of tickers ex. ['AAPL', 'MSFT']
            start_date (str) : Beginning date for the backtest ex. "2023-01-01"
            end_date (str) : End date for the backtest ex. "2024-01-01"
            missing_values_strategy (str): Strategy to handle missing values ('drop' or 'fill_forward'). Default is 'fill_forward'.
        """
        # Type Checks
        if isinstance(tickers, list):
            if not all(isinstance(ticker, str) for ticker in tickers):
                raise TypeError("All items in 'tickers' must be of type string.")
        else:
            raise TypeError("'tickers' must be a list of strings.")
        
        if not isinstance(missing_values_strategy, str) or missing_values_strategy not in ['fill_forward', 'drop']:
            raise ValueError("'missing_value_strategy' must either 'fill_forward' or 'drop' of type str.")

        self._validate_timestamp_format(start_date)
        self._validate_timestamp_format(end_date)

        # Get data from backend
        response = self.data_client.get_bar_data(tickers=tickers, start_date=start_date, end_date=end_date)

        # Process the data
        data = pd.DataFrame(response)
        data.drop(columns=['id'], inplace=True)
        data = self._handle_null_values(data, missing_values_strategy)
        self.data = self._process_bardata(data)
                
        # Storing unique dates if needed
        self.unique_timestamps = self.data['timestamp'].unique().tolist()
        
        return True

    def _validate_timestamp_format(self, timestamp:str):
        # Timestamp format check for ISO 8601
        try:
            # This attempts to parse the timestamp according to the ISO 8601 format.
            datetime.fromisoformat(timestamp)
        except ValueError:
            raise ValueError("Invalid timestamp format. Required format: YYYY-MM-DDTHH:MM:SS")
        except TypeError:
            raise TypeError("'timestamp' must be of type str.")

    def _handle_null_values(self, data:pd.DataFrame, missing_values_strategy: str = "fill_forward"):
       
        if not isinstance(missing_values_strategy, str) or missing_values_strategy not in ['fill_forward', 'drop']:
            raise ValueError("'missing_value_strategy' must either 'fill_forward' or 'drop' of type str.")
       
        data = data.pivot(index='timestamp', columns='symbol')

        # Handle missing values based on the specified strategy
        if missing_values_strategy == 'drop':
            data.dropna(inplace=True)
        elif missing_values_strategy == 'fill_forward':
            if data.iloc[0].isnull().any(): # Check if the first row contains NaN values
                raise ValueError("Cannot forward fill as the first row contains NaN values. Consider using another imputation method or manually handling these cases.")
            
            data.ffill(inplace=True)

        return data.stack(level='symbol', future_stack=True).reset_index()

    def _process_bardata(self, data:pd.DataFrame):
        """ Transform the data provide by the database into the needed format for the backtest. """
        
        # Convert the 'timestamp' column to datetime objects
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Convert the 'timestamp' column from datetime to Unix time (seconds since epoch)
        data['timestamp'] = (data['timestamp'].astype('int64') // 1e9).astype('int')

        # Convert OHLCV columns to floats
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        data[ohlcv_columns] = data[ohlcv_columns].astype(float)

        # Sorting the DataFrame by the 'timestamp' column in ascending order
        return  data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

    def data_stream(self):
        """
        Simulates a market data listener, iterates through the unique dates, callign the setMarketData for each date until finished.
        """
        self.current_date_index += 1

        if self.current_date_index >= len(self.unique_timestamps):
            return False  # No more unique dates
            
        # Update the next_date here
        self.next_date = self.unique_timestamps[self.current_date_index]
        next_day = datetime.fromtimestamp(self.next_date).date() 

        if self.current_day is None or next_day != self.current_day:
            if self.current_day is not None:
            # Perform EOD operations for the previous day
                self.event_queue.put(EODEvent(timestamp=self.current_day))
            # Update the current day
            self.current_day = next_day                    

        self._set_market_data()
        return True
    
    def _get_latest_data(self):
        """ Return the next most recent bar data for all symbols. """
        return self.data[self.data['timestamp'] == self.next_date]

    def _set_market_data(self):
        """
        Sets the MarketDataEvent into the main event queue.
        """
        latest_data_batch = self._get_latest_data()
        result_dict = {}
        for idx, row in latest_data_batch.iterrows():
            ticker = row['symbol']
            result_dict[ticker] = BarData.from_series(row) 
        
        self.order_book.update_market_data(data=result_dict, timestamp=self.next_date)

        




