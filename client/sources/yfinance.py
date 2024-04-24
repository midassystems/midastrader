import numpy as np
import yfinance as yf
from decimal import Decimal
from decouple import config
from shared.market_data import BarData
from client import DatabaseClient
from shared.utils import iso_to_unix

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

    
class YFinanceClient:
    def __init__(self) -> None:
        pass

    def get_historical_data(self, symbols:list, start_date:str, end_date:str, interval='1d'):
        """
        Fetches historical price data for a given stock symbol using yfinance library.

        Parameters:
        symbol (str): The stock symbol to fetch data for.
        start_date (str): Start date for the data in YYYY-MM-DD format.
        end_date (str): End date for the data in YYYY-MM-DD format.
        interval (str): Data interval. Valid intervals: 1d, 1wk, 1mo (default '1d').

        Returns:
        pandas.DataFrame: A DataFrame containing the historical price data.
        """
         # Join symbols into a single string if provided as a list
        if isinstance(symbols, list):
            symbols_str= ' '.join(symbols)
        
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

if __name__ == "__main__":

    # Initialize the database client
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL)
    
    # Initialize YF client
    client = YFinanceClient()
    
    # Variables
    start_date = "2024-01-01"
    end_date ="2024-03-20"
    symbols = ["^GSPC"]

    # Check if symbols exist
    for symbol in symbols:
        if not database.get_symbol_by_ticker(symbol):
            raise Exception(f"{symbol} not present in database.")

    data = client.get_historical_data(symbols,start_date, end_date)  

    # Database client
    response = database.create_bulk_price_data(data)
    print(response)
