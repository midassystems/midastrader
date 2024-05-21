import numpy as np
import yfinance as yf
from typing import List
from decimal import Decimal

from midas.shared.utils import iso_to_unix
from midas.shared.market_data import BarData

class YFinanceClient:
    def __init__(self) -> None:
        pass

    def get_historical_data(self, symbols:list, start_date:str, end_date:str, interval='1d') -> List[BarData]:
        """
        Fetches historical price data for a given stock symbol using yfinance library.

        Parameters:
        - symbol (str): The stock symbol to fetch data for.
        - start_date (str): Start date for the data in YYYY-MM-DD format.
        - end_date (str): End date for the data in YYYY-MM-DD format.
        - interval (str): Data interval. Valid intervals: 1d, 1wk, 1mo (default '1d').

        Returns:
        - List[BarData]: A list containing BarData objects.
        """
        # Join symbols into a single string if provided as a list
        if isinstance(symbols, list):
            symbols_str= ' '.join(symbols)
        
        # Make request
        df = yf.download(symbols_str, start=start_date, end=end_date, interval=interval, group_by='ticker')
        
        data = []
        # Process data for each symbol
        for symbol in symbols:
            # Extract symbol-specific DataFrame
            symbol_df = df[symbol] if len(symbols) > 1 else df
            
            for index, row in symbol_df.iterrows():
                iso_date = index.isoformat()
                timestamp_unix=iso_to_unix(iso_date)
                
                bar = BarData(
                    ticker=symbol,
                    timestamp=np.uint64(timestamp_unix),
                    open=Decimal(row['Open']),
                    high=Decimal(row['High']),
                    low=Decimal(row['Low']),
                    close=Decimal(row['Close']),
                    volume=np.uint64(row['Volume'])
                )
                data.append(bar)

        return data
