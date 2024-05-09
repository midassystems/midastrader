import logging
import pandas as pd
from typing import List
from datetime import datetime

from midas.client import DatabaseClient

logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessing:
    """
    A class responsible for fetching, processing, and preparing financial data from a database for further analysis or backtesting.

    The class is designed to interface with a database client to retrieve historical financial data for specified securities over a given date range. It includes functionality to handle missing values and preprocess the data to fit the requirements of financial analysis or algorithmic trading strategies.

    Attributes:
    - database (DatabaseClient): An instance of a DatabaseClient which provides methods to interact with the database.
    - raw_data (pd.DataFrame): DataFrame to store the raw data retrieved from the database.
    - processed_data (pd.DataFrame): DataFrame to store the processed data ready for analysis or backtesting.

    Methods:
    - get_data(tickers, start_date, end_date, missing_values_strategy): Retrieves and processes data from the database.
    - _validate_timestamp_format(timestamp): Validates the format of timestamp strings.
    - _handle_null_values(data, missing_values_strategy): Handles missing values in the dataset based on a specified strategy.
    - _process_bardata(data): Processes raw data into a structured format suitable for backtesting.
    - _check_duplicates(data): Checks for and reports any duplicate records in the data.
    - check_duplicates(series): Checks for duplicate values in a Pandas Series.
    - check_missing(data): Checks for missing values in a Pandas DataFrame.
    """
    def __init__(self,  database_client: DatabaseClient):
        """
        Initializes the DataProcessing class with a database client.

        Parameters:
        - database_client (DatabaseClient): The database client used to fetch data.
        """
        self.database = database_client
        self.raw_data = None
        self.processed_data = None

    def get_data(self, tickers: List[str], start_date: str, end_date: str, missing_values_strategy: str = 'fill_forward') -> bool:
        """
        Retrieves data from the database and initiates the data processing. The method stores the initial data response in self.raw_data and processed data in self.processed_data.

        Parameters:
        - tickers (List[str]): A list of stock tickers, e.g., ['AAPL', 'MSFT'].
        - start_date (str): The start date for data retrieval in ISO 8601 format, e.g., "2023-01-01".
        - end_date (str): The end date for data retrieval in ISO 8601 format, e.g., "2024-01-01".
        - missing_values_strategy (str): Strategy to handle missing values. Options are 'fill_forward' or 'drop'. Defaults to 'fill_forward'.

        Returns:
        - bool: Returns True if data retrieval and processing are successful.
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
        logging.info(response)

        # Process the data
        data = pd.DataFrame(response)
        data.drop(columns=['id'], inplace=True)
        self._check_duplicates(data)
        data = self._handle_null_values(data, missing_values_strategy)
        self.processed_data = self._process_bardata(data)
        
        return True
    
    def _validate_timestamp_format(self, timestamp: str) -> None:
        """
        Validates the format of the provided timestamp string.

        Parameters:
        - timestamp (str): The timestamp string to validate.
        """
        # Timestamp format check for ISO 8601
        try:
            # This attempts to parse the timestamp according to the ISO 8601 format.
            datetime.fromisoformat(timestamp)
        except ValueError:
            raise ValueError("Invalid timestamp format. Required format: YYYY-MM-DDTHH:MM:SS")
        except TypeError:
            raise TypeError("'timestamp' must be of type str.")

    def _handle_null_values(self, data: pd.DataFrame, missing_values_strategy: str = "fill_forward") -> pd.DataFrame:
        """
        Handles missing values in a DataFrame according to the specified strategy after pivoting the data for time series analysis.

        Parameters:
        - data (pd.DataFrame): The DataFrame with potential missing values.
        - missing_values_strategy (str): The strategy for handling missing values. Options are 'fill_forward' or 'drop'.

        Returns:
        - pd.DataFrame: The DataFrame with missing values handled according to the specified strategy.
        """
       
        if not isinstance(missing_values_strategy, str) or missing_values_strategy not in ['fill_forward', 'drop']:
            raise ValueError("'missing_value_strategy' must either 'fill_forward' or 'drop' of type str.")
       
        data = data.pivot(index='timestamp', columns='symbol')

        # Handle missing values based on the specified strategy
        if missing_values_strategy == 'drop':
            data.dropna(inplace=True)
        elif missing_values_strategy == 'fill_forward':
            # Drop all rows up to the first non-null row
            if data.iloc[0].isnull().any():
                first_complete_index = data.dropna().index[0]
                data = data.loc[first_complete_index:]
            data.ffill(inplace=True)
            
        return data.stack(level='symbol', future_stack=True).reset_index()

    def _process_bardata(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the raw data fetched from the database into a structured format suitable for backtesting.
        This includes converting timestamps to datetime objects and numeric data types for financial metrics.

        Parameters:
        - data (pd.DataFrame): The raw data DataFrame with columns for 'timestamp' and OHLCV values.

        Returns:
        - pd.DataFrame: The processed DataFrame with timestamps sorted and data ready for analysis.
        """
        # Convert OHLCV columns to floats
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        data[ohlcv_columns] = data[ohlcv_columns].astype(float)

        data = data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        return data

    # -- Checks -- 
    def _check_duplicates(self, data: pd.DataFrame) -> None:
        """
        Checks for and prints out any duplicate records in the data, based on 'timestamp' and 'symbol'.

        Parameters:
        - data (pd.DataFrame): The DataFrame to check for duplicates.

        Side Effect:
        - Prints out duplicate rows if found.
        """
        duplicates = data.duplicated(subset=['timestamp', 'symbol'], keep=False)
        if duplicates.any():
            print("Duplicates found:")
            print(data[duplicates])

    def check_duplicates_series(self, series: pd.Series) -> bool:
        """
        Checks for duplicate values within a Pandas Series.

        Parameters:
        - series (pd.Series): The series to check for duplicates.

        Returns:
        - bool: True if duplicates are found, False otherwise.
        """
        duplicate_dates = series.duplicated()
        return any(duplicate_dates)
    
    def check_missing(self, data: pd.DataFrame) -> bool:
        """
        Checks a DataFrame for any missing values.

        Parameters:
        - data (pd.DataFrame): The DataFrame to check for missing values.

        Returns:
        - bool: True if any missing values are found, otherwise False.
        """
        has_missing_values = data.isna().any().any()  # Checks if any column has any NA values
        return has_missing_values

    