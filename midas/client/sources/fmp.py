import json
import requests
import pandas as pd
from enum import Enum
from decouple import config
from ..client import DatabaseClient, SecurityType, Exchange,Indsutry, Currency, ContractUnits, AssetClass



DATABASE_KEY = config('MIDAS_API_KEY')
DATABASE_URL = config('MIDAS_URL')

    
class FMPClient:
    def __init__(self, api_key:str, api_url:str ='https://financialmodelingprep.com/api/v3/'):
        self.api_url = api_url
        self.api_key = api_key

    def get_historical_data(self, symbol, start_date, end_date, serietype='line'):
        """
        Fetches historical price data for a given stock symbol using requests library.

        Parameters:
        symbol (str): The stock symbol to fetch data for.
        start_date (str): Start date for the data in YYYY-MM-DD format.
        end_date (str): End date for the data in YYYY-MM-DD format.
        serietype (str): Type of data series ('line' by default).

        Returns:
        dict: A dictionary containing the historical price data.
        """
        url = f"{self.api_url}historical-price-full/{symbol}"
        params = {
            'apikey': self.api_key,
            'from': start_date,
            'to': end_date,
            'serietype': serietype
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to fetch historical data: {response.text}")
    
    def get_available_indexes(self):
        """
        Fetches available indexes from the FinancialModelingPrep API.
            > https://financialmodelingprep.com/api/v3/symbol/available-indexes?apikey=8415942f9c72bf0c64ff9efb2a028add

        Returns:
        dict: A dictionary or list containing the available indexes.
        """
        # The API key is included directly in the URL, so you don't need to specify it again in the params.
        url = f"{self.api_url}symbol/available-indexes?apikey={self.api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to fetch available indexes: {response.text}")

if __name__ == "__main__":
    # Initialize the database client
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL)
    
    # Initialize FMP client
    client = FMPClient(config('FMP_PRIMARY'))
    
    start_date = "2024-01-01"
    end_date="2024-01-19"
    symbols = ['AAPL']

    # Check and create assets if they don't exist
    # for symbol in symbols:
    #     if not database.get_symbol_by_ticker(symbol):
    #         raise Exception(f"{symbol} not present in database.")

    data = client.get_historical_data(symbols,start_date, end_date)    
    print(data)

    # # Database client
    # response = database.create_bulk_price_data(data)
    # print(response)


    # -- Create Index --
    # GSPC = {
    #     'ticker':'^GSPC',
    #     'name':'S&P 500',
    #     'currency':Currency.USD,
    #     'security_type':SecurityType.INDEX,
    #     'asset_class': AssetClass.EQUITY
    #     }
    # database.create_index(**GSPC)