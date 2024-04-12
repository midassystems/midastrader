import requests
import pandas as pd
from enum import Enum
from queue import Queue
from typing import List, Dict
from datetime import datetime, timedelta

class AssetClass(Enum):
    EQUITY = 'EQUITY'
    COMMODITY = 'COMMODITY'
    FIXED_INCOME ='FIXED_INCOME'
    FOREX='FOREX'
    CRYPTOCURRENCY='CRYPTOCURRENCY'
    
class SecurityType(Enum):
    EQUITY = 'EQUITY'
    FUTURE = 'FUTURE'
    OPTION = 'OPTION'
    INDEX = 'INDEX'

class Exchange(Enum):   
    NASDAQ = 'NASDAQ'
    CME = 'CME'                   

class Currency(Enum):   
    USD='USD'
    CAD='CAD'   
    EUR='EUR'
    GBP='GBP'
    AUD='AUD'           
    JPY='JPY'

class Indsutry(Enum):
    # Equities
    ENERGY='Energy'
    MATERIALS='Materials'
    INDUSTRIALS='Industrials'
    UTILITIES='Utilities'
    HEALTHCARE='Healthcare'
    FINANCIALS='Financials'
    CONSUMER='Consumer'
    TECHNOLOGY='Technology'
    COMMUNICATION='Communication'
    REAL_ESTATE='Real Estate'   
    
    # Commodities
    METALS='Metals' 
    AGRICULTURE='Agriculture'
    #ENERGY         

class ContractUnits(Enum):
    BARRELS='Barrels'
    BUSHELS='Bushels'
    POUNDS='Pounds'
    TROY_OUNCE='Troy Ounce'
    METRIC_TON='Metric Ton'
    SHORT_TON='Short Ton'

class DatabaseClient:
    def __init__(self, api_key:str, api_url:str ='http://127.0.0.1:8000'):
        self.api_url = api_url
        self.api_key = api_key

    # -- Helper Data -- 
    def create_asset_class(self, **asset_class_data):
        """
        Creates a new asset class.

        Parameters:
        asset_class_data (dict):
            name (str): The name of the asset class.
            description (str): The description of the asset class.
        """
        required_keys = {
            "name": AssetClass,
            "description": str,  
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in asset_class_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(asset_class_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(asset_class_data[key]).__name__}")

        # Prepare the data payload
        data = {
            "name": asset_class_data['name'].value,
            "description": asset_class_data['description']
        }

        url = f"{self.api_url}/api/asset_class/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Asset class creation failed: {response.text}")
        return response.json() 
    
    def get_asset_classes(self):
        """
        Retrieves all asset classes.
        """
        url = f"{self.api_url}/api/asset_class/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching asset classes failed: {response.text}")
        return response.json()
    
    def update_asset_class(self, asset_class_id: int, **updates):
        """
        Updates the description of an existing asset class.

        Parameters:
        asset_class_id (int): The ID of the asset class to update.
        description (str): The new description for the asset class.
        """
        url = f"{self.api_url}/api/asset_class/{asset_class_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Asset class update failed: {response.text}")
        return response.json()

    def create_currency(self, **currency_data):
        """
        Creates a new currency.

        Parameters:
        currency_data(dict):
            code (str): The currency code (e.g., USD).
            name (str): The name of the currency (e.g., US Dollar).
            region (str): The region or country where the currency is used.
        """
        required_keys = {
            "code": Currency, 
            "name": str, 
            "region": str
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in currency_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(currency_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(currency_data[key]).__name__}")
        
        
        data = {
            "code": currency_data['code'].value,
            "name": currency_data['name'],
            "region": currency_data['region']
        }

        url = f"{self.api_url}/api/currency/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Currency creation failed: {response.text}")
        return response.json()

    def get_currencies(self):
        """
        Retrieves all currencies.
        """
        url = f"{self.api_url}/api/currency/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching currencies failed: {response.text}")
        return response.json()

    def update_currency(self, currency_id: int, **updates):
        """
        Updates information for an existing currency.

        Parameters:
        currency_id (int): The ID of the currency to update.
        **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url = f"{self.api_url}/api/currency/{currency_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Currency update failed: {response.text}")
        return response.json()
    
    # -- Indexes -- 
    def create_index(self, **index_data):
        """
        Creates a new index.

        Parameters:
        index_data (dict):
            ticker (str): The ticker symbol of the benchmark.
            security_type (str): The type of security, e.g., "BENCHMARK".
            name (str): The name of the benchmark.
            asset_class (str): The asset class the benchmark belongs to.
            currency (str): The currency of the benchmark.
        """
        required_keys = {
            "ticker": str, 
            "security_type": SecurityType,  
            "name": str, 
            "asset_class": AssetClass, 
            "currency":Currency
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in  index_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(index_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(index_data[key]).__name__}")

        data = {
            "symbol_data": {
                "ticker": index_data['ticker'],
                "security_type": index_data['security_type'].value
            },
            "name": index_data['name'],
            "asset_class": index_data['asset_class'].value,
            "currency": index_data['currency'].value
        }

        url = f"{self.api_url}/api/indexes/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Benchmark creation failed: {response.text}")
        return response.json()
    
    def get_indexes(self):
        """
        Retrieves all benchmarks.
        """
        url = f"{self.api_url}/api/indexes/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    def update_index(self, index_id: int, **updates):
        """
        Updates information for an existing benchmark.

        Parameters:
        benchmark_id (int): The ID of the benchmark to update.
        **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url = f"{self.api_url}/api/indexes/{index_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Index update failed: {response.text}")
        return response.json()

    # -- Equity -- 
    def create_equity(self, **equity_data):
        """
        **equity_data = {
            "ticker": str,
            "security_type": SecurityType,  
            "company_name": str,
            "exchange": Exchange,       
            "currency": Currency,       
            "industry": Indsutry,  
            "market_cap": int,
            "shares_outstanding": int
        }
        
        """
        required_keys = {
            "ticker": str,
            "security_type": SecurityType,  
            "company_name": str,
            "exchange": Exchange,       
            "currency": Currency,       
            "industry": Indsutry,  
            "market_cap": int,
            "shares_outstanding": int
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in equity_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(equity_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(equity_data[key]).__name__}")

        # Prepare the data payload
        data = {
            "symbol_data": {
                "ticker": equity_data["ticker"],
                "security_type": equity_data["security_type"].value
            },
            "company_name": equity_data["company_name"],
            "exchange": equity_data["exchange"].value,
            "currency": equity_data["currency"].value,
            "industry": equity_data["industry"].value,
            "market_cap": equity_data["market_cap"],
            "shares_outstanding": equity_data["shares_outstanding"]
        }
        url = f"{self.api_url}/api/equities/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            raise ValueError(f"Asset creation failed: {response.text}")
        return response.json()

    def get_equity(self):
        """
        Retrieves all benchmarks.
        """
        url = f"{self.api_url}/api/equities/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    def update_equity(self, equity_id: int, **updates):
        """
        Updates information for an existing benchmark.

        Parameters:
        benchmark_id (int): The ID of the benchmark to update.
        **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url = f"{self.api_url}/api/equities/{equity_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Equity update failed: {response.text}")
        return response.json()

    # -- Future --
    def create_future(self, **future_data):
        """    
        future_data = {
            "ticker": str,
            "security_type": SecurityType,  
            "product_code":str,
            "product_name": str,
            "exchange": Exchange,       
            "currency": Currency,       
            "contract_size":int,    
            "contract_units":ContractUnits,
            "tick_size":float,   
            "min_price_fluctuation":float,    
            "continuous":bool
        }
        """
        
        required_keys = {
            "ticker": str,
            "security_type": SecurityType,  
            "product_code":str,
            "product_name": str,
            "exchange": Exchange,       
            "currency": Currency,       
            "contract_size":int,    
            "contract_units":ContractUnits,
            "tick_size":float,   
            "min_price_fluctuation":float,    
            "continuous":bool
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in future_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(future_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(future_data[key]).__name__}")
        
        data = {
                'symbol_data': {
                    'ticker': future_data['ticker'],
                    'security_type': future_data['security_type'].value
                    },

                'product_code':future_data['product_code'],
                'product_name':future_data['product_name'], 
                'exchange':future_data['exchange'].value,
                'currency':future_data['currency'].value,
                'contract_size':future_data['contract_size'],
                'contract_units':future_data['contract_units'].value,
                'tick_size':future_data['tick_size'],
                'min_price_fluctuation':future_data['min_price_fluctuation'],
                'comtinuous':future_data['continuous']
                }
        
        url = f"{self.api_url}/api/futures/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            raise ValueError(f"Asset creation failed: {response.text}")
        return response.json()
    
    def get_future(self):
        """
        Retrieves all benchmarks.
        """
        url = f"{self.api_url}/api/futures/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()
    
    def update_future(self, future_id: int, **updates):
        """
        Updates information for an existing benchmark.

        Parameters:
        benchmark_id (int): The ID of the benchmark to update.
        **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url = f"{self.api_url}/api/futures/{future_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Equity update failed: {response.text}")
        return response.json()

    # -- Symbol -- 
    def get_symbol_by_ticker(self, ticker: str):
        url = f"{self.api_url}/api/symbols/"
        params = {'ticker': ticker}
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise ValueError(f"Failed to retrieve asset by symbol: {response.text}")
    
    def get_symbol(self):
        url = f"{self.api_url}/api/symbols/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve assets: {response.text}")
        return response.json()
    
    # -- Bar Data -- 
    def create_bar_data(self, **bar_data):
        """
        Creates new bar data.

        Parameters:
        bar_data (dict): The bar data to be created with required keys.
            symbol (str)
            timestamp (str)  
            open (float)
            close (float)
            high (float)
            low (float)
            volume (float)
        """
        # Define the required keys and their expected types
        required_keys = {
            "symbol": str,
            "timestamp": str,  # Assuming timestamp is a string; adjust the type as needed
            "open": float,
            "close": float,
            "high": float,
            "low": float,
            "volume": int,  # Adjust types based on your specific requirements
        }

        # Check for missing required keys and type validation
        for key, expected_type in required_keys.items():
            if key not in bar_data:
                raise ValueError(f"{key} is required.")
            if not isinstance(bar_data[key], expected_type):
                raise TypeError(f"Incorrect type for {key}. Expected {expected_type.__name__}, got {type(bar_data[key]).__name__}")

        # Prepare the data payload by filtering bar_data against required_keys
        data = {key: bar_data[key] for key in required_keys}

        url = f"{self.api_url}/api/bardata/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)

        # Handle the response
        if response.status_code != 201:
            raise ValueError(f"Bar data creation failed: {response.text}")
        return response.json()

    def create_bulk_price_data(self, bulk_data: List[Dict]):
        batch_size = 400
        total_batches = len(bulk_data) // batch_size + (1 if len(bulk_data) % batch_size > 0 else 0)
        all_responses = []

        for batch_number in range(total_batches):
            # Extract the current batch
            start_index = batch_number * batch_size
            end_index = start_index + batch_size
            current_batch = bulk_data[start_index:end_index]

            # Send the batch request
            url = f"{self.api_url}/api/bardata/bulk_create/"
            headers = {'Authorization': f'Token {self.api_key}'}
            response = requests.post(url, json=current_batch, headers=headers)

            if response.status_code != 201:
                raise ValueError(f"Bulk bar data creation failed for batch {batch_number + 1}: {response.text}")
            
            all_responses.append(response.json())

        # Aggregate all responses
        aggregated_response = {
            'total_batches': total_batches,
            'batch_responses': all_responses
        }
        return aggregated_response
    
    def get_bar_data(self, tickers: List[str], start_date: str = None, end_date: str = None):
        if start_date is None or end_date is None:
            raise ValueError("Start date and end date must be provided for batching")

        batch_size = 50
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        current_start = start
        all_data = []
        # print(all_data)

        while current_start < end:
            current_end = min(current_start + timedelta(days=batch_size), end)
            # Adjust the end date to avoid including it in the next batch
            adjusted_end_date = (current_end - timedelta(days=1)).strftime('%Y-%m-%d') if current_end != end else current_end.strftime('%Y-%m-%d')

            batch_data = self._fetch_batch_data(tickers, current_start.strftime('%Y-%m-%d'), adjusted_end_date)
            all_data.extend(batch_data)
            # Set the start of the next batch to the day after the current batch's end
            current_start = current_end
        return all_data 

    def _fetch_batch_data(self, tickers, start_date, end_date):
        url = f"{self.api_url}/api/bardata/"
        params = {
            'tickers': ','.join(tickers),
            'start_date': start_date,
            'end_date': end_date
        }
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve bar data for batch {start_date} to {end_date}: {response.text}")

        return response.json()
    
    def update_bar_data(self, bar_id: int, **updates):
        """
        Updates information for an existing benchmark.

        Parameters:
        benchmark_id (int): The ID of the benchmark to update.
        **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url = f"{self.api_url}/api/bardata/{bar_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = updates
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Equity update failed: {response.text}")
        return response.json()

    def get_benchmark_data(self, tickers: List[str], start_date: str = None, end_date: str = None):
        data = self.get_bar_data(tickers, start_date, end_date)
        return [{'timestamp': item['timestamp'], 'close': item['close']} for item in data]
    
    # -- Backtest Data -- 
    def create_backtest(self, data):
        """
        Create a new backtest.
        :param data: Dictionary containing backtest data.
        :return: Response from the API.
        """
        url = f"{self.api_url}/api/backtest/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Backtest creation failed: {response.text}")
        return response.json()

    def get_backtests(self):
        """
        Retrieve all backtests.
        :return: List of backtests.
        """
        url = f"{self.api_url}/api/backtest/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers = {'Authorization': f'Token {self.api_key}'})

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve backtests: {response.text}")
        return response.json()

    def get_specific_backtest(self, backtest_id):
        """
        Retrieve a specific backtest by ID.
        :param backtest_id: ID of the backtest to retrieve.
        :return: Backtest data.
        """
        url = f"{self.api_url}/api/backtest/{backtest_id}/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve backtest: {response.text}")
        return response.json()

    # -- Live Session Data -- 
    def create_live_session(self, data):
        """
        Create a new live session.
        :param data: Dictionary containing live session data.
        :return: Response from the API.
        """
        url = f"{self.api_url}/api/live_session/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"LiveSession creation failed: {response.text}")
        return response.json()

    def get_live_sessions(self):
        """
        Retrieve all live_sessionss.
        :return: List of live_sessionss.
        """
        url = f"{self.api_url}/api/live_session/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve live_sessions: {response.text}")
        return response.json()

    def get_specific_live_session(self, live_session_id):
        """
        Retrieve a specific live_session by ID.
        :param live_session_id: ID of the live_session to retrieve.
        :return: LiveSession data.
        """
        url = f"{self.api_url}/api/live_session/{live_session_id}/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve live_session: {response.text}")
        return response.json()

    # -- Live Session --
    def create_session(self, session_id: int):
        """
        Creates session instance for current live session.

        Parameters:
            session_id(int) : Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        data = { "session_id" : session_id }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Session creation failed: {response.text}")
        return response.json()
    
    def delete_session(self, session_id: int):
        """
        Creates session instance for current live session.

        Parameters:
            session_id(int) : Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)
        
        if response.status_code != 204:
            raise ValueError(f"Session deletion failed: {response.text}")

    def create_positions(self, session_id, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Position creation failed: {response.text}")
        return response.json()
    
    def update_positions(self, session_id:int, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Position update failed: {response.text}")
        return response.json()
    
    def get_positions(self, session_id:int):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Position get failed: {response.text}")
        return response.json()

    def create_orders(self, session_id, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Order creation failed: {response.text}")
        return response.json()
    
    def update_orders(self, session_id:int, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order update failed: {response.text}")
        return response.json()
    
    def get_orders(self, session_id:int):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order get failed: {response.text}")
        return response.json()

    def create_account(self, session_id, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Order creation failed: {response.text}")
        return response.json()
    
    def update_account(self, session_id:int, data):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order update failed: {response.text}")
        return response.json()
    
    def get_account(self, session_id:int):
        """
        Updates position information on current live session. ** Stored in temporary in-memory store. **

        Parameters:
            **updates: Arbitrary number of keyword arguments representing the fields to update.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order get failed: {response.text}")
        return response.json()

