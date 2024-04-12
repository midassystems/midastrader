import pandas as pd
from typing import List
from decouple import config
from datetime import datetime

from client import DatabaseClient

class DataProcessing:
    def __init__(self,  database_client: DatabaseClient) -> None:
        self.database = database_client
        self.raw_data = None
        self.processed_data = None

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
        response = self.database.get_bar_data(tickers=tickers, start_date=start_date, end_date=end_date)

        # Process the data
        data = pd.DataFrame(response)
        data.drop(columns=['id'], inplace=True)
        data = self._handle_null_values(data, missing_values_strategy)
        self.processed_data = self._process_bardata(data)
        
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
            # Check if the first row contains NaN values
            if data.iloc[0].isnull().any():
            # Since there's no value to forward fill from, raise an error
                raise ValueError("Cannot forward fill as the first row contains NaN values. Consider using another imputation method or manually handling these cases.")
            
            data.ffill(inplace=True)

        return data.stack(level='symbol', future_stack=True).reset_index()

    def _process_bardata(self, data: pd.DataFrame):
        """ Transform the data provide by the database into the needed format for the backtest. """
        
        # Convert the 'timestamp' column to datetime objects
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Convert OHLCV columns to floats
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        data[ohlcv_columns] = data[ohlcv_columns].astype(float)

        data = data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        return data.pivot(index='timestamp', columns='symbol', values='close')

    # -- Checks -- 
    def check_duplicates(self, series: pd.Series) -> bool:
        """Check for duplicate values in a Pandas Series.

        Args:
            series (pd.Series): The series to check for duplicates.

        Returns:
            bool: True if duplicates are found, False otherwise.
        """
        duplicate_dates = series.duplicated()
        return any(duplicate_dates)
    
    def check_missing(self, data: pd.DataFrame) -> bool:
        """Check for missing values in a Pandas DataFrame.

        Args:
            data (pd.DataFrame): The DataFrame to check for missing values.

        Returns:
            bool: True if missing values are found, False otherwise.
        """
        has_missing_values = data.isna().any().any()  # Checks if any column has any NA values
        return has_missing_values

    